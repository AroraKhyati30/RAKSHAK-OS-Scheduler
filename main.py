# ==========================================
# 1. IMPORTS
# ==========================================

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Annotated, Literal
import string
import secrets
from psycopg2.extras import Json
import psycopg2, os
from tokenizers import Tokenizer
import ollama
import json
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn, fastapi
from os_module.models import Victim, RescueTeam
from os_module.scheduler import dispatch_next
# ==========================================
# 2. ENVIRONMENT & APP INITIALIZATION
# ==========================================
# Load the env file to access Postgres credentials securely
load_dotenv()

# Load a pre-trained fast tokenizer (e.g., standard BERT) to manage text length for the AI
tokenizer = Tokenizer.from_pretrained("bert-base-uncased")

# Initialize the FastAPI application instance
app = FastAPI()

# Mount static folder to serve frontend assets (HTML, CSS, JS)
#app.mount("/static", StaticFiles(directory="src"), name="static")

# configuring CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["*"],  # Permits incoming requests from System 1
    allow_origins= "https://rakshak-frontend-src.vercel.app/",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# 3. PYDANTIC MODELS (Data Validation)
# ==========================================
# Defines the expected payload when a victim submits a distress signal
class DistressRequest(BaseModel):
    raw_message: str = Field(..., description='Message of the victim')
    latitude: float = Field(..., ge=-90.0, le=90.0, example=30.3165)
    longitude: float = Field(..., ge=-180.0, le=180.0, example=78.0322)

# Defines the structured response sent back to the victim
class DistressResponse(BaseModel):
    token_id: str
    status: str
    extracted_data: dict
    message: str

# Defines the expected payload when registering a new rescue team
class RescueRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, example=30.3165)
    longitude: float = Field(..., ge=-180.0, le=180.0, example=78.0322)
    team_capacity: int = Field(..., ge=5)

# Defines the structured response after a rescue team registers
class RescueResponse(BaseModel):
    team_id: str
    status: Literal['Available', 'In_Transit', 'Assigned']
    message: str

class RescueCompleteRequest(BaseModel):
    token_id: str = Field(..., description="The unique token ID of the rescued victim")
    team_id: str = Field(..., description="The ID of the rescue team completing the operation")


# ==========================================
# 4. HELPER & UTILITY FUNCTIONS
# ==========================================
# establish the connection with database using environment variables
def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        sslmode="require"  # This is mandatory for Supabase
    )

# token id generation to create an anonymous tracking ID (PID paradigm) for victims
def distress_token_id_generator(prefix="TK-2026-UK") -> str:
    random_chars = ''.join(
        secrets.choice(string.ascii_uppercase + string.digits)
        for _ in range(6)
    )
    return f"{prefix}-{random_chars}"

# team_id generation to uniquely identify rescue units
def rescue_team_id_generator(prefix='UK-2026-RES') -> str:
    random_chars = ''.join(
        secrets.choice (string.ascii_uppercase + string.digits)
        for _ in range(4)
    )
    return f"{prefix}-{random_chars}"

# Passes the raw message to a local LLM to extract structured severity and vulnerability metrics
def extract_disaster_metrics(text: str) -> dict:
    # 1. Hugging Face Tokenization: Convert text into AI token IDs
    encoded = tokenizer.encode(text)
    
    # 2. Truncate strictly to your safety limit (e.g., max 120 tokens)
    truncated_ids = encoded.ids[:120]
    
    # 3. Decode the token IDs back into a clean string for Ollama
    clean_text = tokenizer.decode(truncated_ids)
    
    system_prompt = (
        "You are an emergency response AI. Extract details from the distress text. "
        "Respond ONLY with valid JSON containing these exact keys: "
        "'severity' (integer 1 to 5), "
        "'vulnerability' (integer 1 to 5 based on age or medical conditions) "
    )

    try:
        response = ollama.chat(
            model="qwen2.5:3b",
            format="json",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": clean_text}
            ]
        )
        return json.loads(response["message"]["content"])
    except Exception:
        # Fallback safe defaults if AI service encounters an issue
        return {"severity": 3, "vulnerability": 3}


# ==========================================
# 5. API ROUTES
# ==========================================

# Route to serve the frontend interface
@app.get("/")
async def serve_index():
    return FileResponse(os.path.join("src", "index.html"))


# post through telegram
@app.post("/api/telegram")
async def telegram_webhook(request: Request):
    telegram_payload = await request.json()
    
    # 1. Extract message details
    message = telegram_payload.get("message", {})
    raw_text = message.get("text")
    chat_id = message.get("chat", {}).get("id")
    
    if not raw_text:
        return {"status": "ignored"}

    # Mock coordinates for simulation (can also be extracted if user shares location)
    latitude = 30.3165
    longitude = 78.0322

    # 2. Run the RAKSHAK pipeline
    token_id = distress_token_id_generator()
    extracted_data = extract_disaster_metrics(raw_text) # extracted_data: python object (dict)
    severity = int(extracted_data.get("severity") or 3)
    vulnerability = int(extracted_data.get("vulnerability") or 3)

    # 3. Insert into PostgreSQL with PostGIS
    conn = None
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            insert_sql = """
                INSERT INTO DistressTickets (
                    token_id, raw_message, extracted_json, location, severity, vulnerability, status
                )
                VALUES (
                    %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, %s, 'Pending'
                );
            """
            cur.execute(
                insert_sql,
                (token_id, raw_text, Json(extracted_data), longitude, latitude, severity, vulnerability)
            )
            conn.commit()

    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database insertion failed: {e}")
    finally:
        if conn:
            conn.close()

    return {"status": "ok", "token_id": token_id}


# request going to db by victim to log their distress call
@app.post('/api/reportDistress', response_model=DistressResponse, status_code=201)
def report_distress(distress_data: DistressRequest):

    # Generate a unique tracker and extract data via Ollama
    token_id = distress_token_id_generator()
    extracted_data = extract_disaster_metrics(distress_data.raw_message)
    extracted_json = Json(extracted_data)
    
    # Dynamically extract metrics rather than using hardcoded values
    severity = int(extracted_data.get("severity") or 3)
    vulnerability = int(extracted_data.get("vulnerability") or 3)

    conn = None

    # SQL string mapping coordinates to a PostGIS spatial point (SRID 4326)
    insert_sql_query = """
        INSERT INTO DistressTickets (
            token_id, raw_message, extracted_json, location, severity, vulnerability, status
        )
        VALUES (
            %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, %s, 'Pending'
        );
    """

    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Execute database insertion
            cur.execute(insert_sql_query, (
                    token_id,
                    distress_data.raw_message,
                    extracted_json,
                    distress_data.longitude,
                    distress_data.latitude,
                    severity,
                    vulnerability
                    )
            )
        # Finalize the transaction
        conn.commit()

    except Exception as e:
        # Revert changes if the database operation fails
        if conn:
            conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Database Error. Error: {str(e)}"
        )

    finally:
        # Always close connection to prevent connection pooling limits
        if conn:
            conn.close()

    # Return tracking token and parsed metadata to caller
    return DistressResponse(
        token_id=token_id,
        status="Pending",
        extracted_data = extracted_data,
        message="Distress report registered successfully. Keep your tracking token safe."
    )

# get data from Distress table for the command dashboard
@app.get('/api/getDistress')
async def get_distress():

    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()

        # Query all active distress tickets
        query = """
        SELECT *
        FROM DistressTickets
        """
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

            # Map tuples to a list of dictionaries for clean JSON response
            result = []
            for row in rows:
                result.append({
                    "token_id" : row[0],
                    "raw_message" : row[1], 
                    "extracted_json" : row[2], 
                    "location" : row[3], 
                    "severity" : row[4], 
                    "vulnerability" : row[5],
                    "wait_time_start" : row[6],
                    "vwps_score" : row[7],
                    "status" : row[8]
                })

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error. Error: {str(e)}"
        )

    finally:
        if connection:
            connection.close()

# Register a new rescue team to the system
@app.post('/api/rescue', response_model=RescueResponse, status_code=201)
async def post_rescue(rescue_data:RescueRequest):

    # Create a unique ID for the team
    team_id = rescue_team_id_generator()

    connection = None
    cursor = None

    try:
        connection = get_db_connection()

        # Insert team with PostGIS spatial point
        query = """
        INSERT INTO RescueTeams (
        team_id, current_location, team_capacity)
        VALUES (%s,  ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s)
        """

        with connection.cursor() as cursor:
            cursor.execute(query, (
                team_id,
                rescue_data.longitude,
                rescue_data.latitude,
                rescue_data.team_capacity
            ))

        # Commit transaction
        connection.commit()

    except Exception as e:
        if connection:
            connection.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Database Error. Error: {str(e)}"
        )

    finally:
        if connection:
            connection.close()

    return RescueResponse(
        team_id=team_id,
        status="Available",
        message="The Rescue has been registered."
    )

# Retrieve all active rescue teams for the dashboard
@app.get('/getRescue')
async def get_rescue():

    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()

        query = """
        SELECT *
        FROM RescueTeams
        """
        with connection.cursor() as cursor:
            cursor.execute(query)

            rows = cursor.fetchall()

            result = []
            for row in rows:
                result.append({
                    "team_id" : row[0],
                    "location" : row[1], 
                    "status": row[2],
                    "capacity" : row[3]
                })

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error. Error: {str(e)}"
        )

    finally:
        if connection:
            connection.close()

# # Triggers the VWPS spatial matching algorithm to dispatch the nearest team

@app.post('/api/dispatch/run')
async def run_dispatch():
    conn = None

    try:
        conn = get_db_connection()

        with conn.cursor() as cursor:
            # Lock one pending victim and all available teams.
            cursor.execute("""
                SELECT
                    token_id,
                    severity,
                    vulnerability,
                    wait_time_start,
                    ST_Y(location) AS latitude,
                    ST_X(location) AS longitude
                FROM distresstickets
                WHERE status = 'Pending'
                ORDER BY wait_time_start ASC
                FOR UPDATE SKIP LOCKED
            """)
            victim_rows = cursor.fetchall()

            cursor.execute("""
                SELECT
                    team_id,
                    team_capacity,
                    ST_Y(current_location) AS latitude,
                    ST_X(current_location) AS longitude
                FROM rescueteams
                WHERE status = 'Available'
                FOR UPDATE SKIP LOCKED
            """)
            team_rows = cursor.fetchall()

            if not victim_rows:
                raise HTTPException(
                    status_code=404,
                    detail="No pending victims found."
                )

            if not team_rows:
                raise HTTPException(
                    status_code=404,
                    detail="No available rescue teams found."
                )

            # Use elapsed seconds so the existing OS scheduler
            # can apply its waiting-time and starvation rules.
            from datetime import datetime, timezone

            now = datetime.now(timezone.utc)

            victims = []
            for row in victim_rows:
                token, severity, vulnerability, arrival, lat, lon = row

                if arrival is None:
                    arrival_seconds = 0.0
                else:
                    arrival_seconds = -(
                        now - arrival
                    ).total_seconds()

                victims.append(
                    Victim(
                        victim_id=token,
                        zone_id=f"Zone-{round(lat, 2)}-{round(lon, 2)}",
                        severity=max(1, min(5, severity or 3)),
                        vulnerability=max(
                            1, min(5, vulnerability or 3)
                        ),
                        arrival_time=arrival_seconds,
                        latitude=lat,
                        longitude=lon,
                    )
                )

            teams = [
                RescueTeam(
                    team_id=row[0],
                    latitude=row[2],
                    longitude=row[3],
                    resources=[],
                )
                for row in team_rows
            ]

            
            # Team resources are not stored in the current schema.
            # Empty resource lists allow nearest-team selection.
            result = dispatch_next(victims, teams, 0.0)


            if result.get("message") != "Rescue team dispatched":
                raise HTTPException(
                    status_code=409,
                    detail=result
                )

            victim_token = result["victim_id"]
            team_id = result["team_id"]

            # Persist the dispatch atomically.
            cursor.execute("""
                UPDATE distresstickets
                SET status = 'Dispatched'
                WHERE token_id = %s AND status = 'Pending'
            """, (victim_token,))

            if cursor.rowcount != 1:
                raise HTTPException(
                    status_code=409,
                    detail="Victim was already dispatched."
                )

            cursor.execute("""
                UPDATE rescueteams
                SET status = 'In_Transit'
                WHERE team_id = %s AND status = 'Available'
            """, (team_id,))

            if cursor.rowcount != 1:
                raise HTTPException(
                    status_code=409,
                    detail="Rescue team is no longer available."
                )

            cursor.execute("""
                INSERT INTO dispatch_logs
                    (token_id, team_id, rescue_status)
                VALUES (%s, %s, 'In Process')
            """, (victim_token, team_id))

        conn.commit()

        return {
            "status": "Success",
            "assigned_victim": victim_token,
            "assigned_team": team_id,
            "priority_type": result.get("priority_type"),
            "zone_scores": result.get("zone_scores", {}),
        }

    except HTTPException:
        if conn:
            conn.rollback()
        raise

    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            conn.close()


# Retrieve the history of all automated dispatch events
@app.get('/getDispatchLogs')
async def getDispatchLogs():

    conn = None
    cur = None

    try:
        conn = get_db_connection()

        query = """
        SELECT *
        FROM Dispatch_Logs
        """

        with conn.cursor() as cur:
            cur.execute(query)

            rows = cur.fetchall()

            result = []
            for row in rows:
                result.append({
                    'log_id': row[0],
                    'token_id': row[1],
                    'team_id': row[2],
                    'dispatch_time': row[3],
                    'rescue_status': row[4], # Maps the newly added 'rescue_status' column
                    'sns_alert_sent': row[5]
                })

            return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error. Error: {str(e)}"
        )
    
    finally:
        if conn:
            conn.close()


@app.post('/api/dispatch/complete', status_code=200)
async def complete_rescue(payload: RescueCompleteRequest):
    connection = None
    
    try:
        connection = get_db_connection()
        
        # 1. Update the dispatch log to reflect completion
        query_log = """
            UPDATE Dispatch_Logs 
            SET rescue_status = 'Completed' 
            WHERE token_id = %s AND team_id = %s
        """
        
        # 2. Mark the victim's ticket as 'Resolved' rather than deleting it for audit trails
        query_victim = """
            UPDATE DistressTickets 
            SET status = 'Resolved' 
            WHERE token_id = %s
        """
        
        # 3. Free up the rescue team so the VWPS algorithm can assign them a new victim
        query_team = """
            UPDATE RescueTeams 
            SET status = 'Available' 
            WHERE team_id = %s
        """
        
        with connection.cursor() as cursor:
            # Execute all three updates in a single ACID transaction
            cursor.execute(query_log, (payload.token_id, payload.team_id))
            cursor.execute(query_victim, (payload.token_id,))
            cursor.execute(query_team, (payload.team_id,))
            
            # Permanently save the state changes to the database
            connection.commit()
            
        return {
            "status": "Success",
            "message": f"Rescue operation for {payload.token_id} completed. Team {payload.team_id} is now available."
        }
        
    except Exception as e:
        if connection:
            connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if connection:
            connection.close()

# This block ensures it always runs on 0.0.0.0:8000 when executed directly
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)