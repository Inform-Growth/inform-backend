from fastapi import APIRouter, HTTPException, Path, Query
from app.db.supabase_connection import SupabaseConnection


router = APIRouter()

db = SupabaseConnection()

@router.get("/{id}", response_model=dict)
async def handle_initial_submission(id: str):
    form_id = id
    result = db.get_form(form_id)
    if result is None:
        raise HTTPException(status_code=404, detail="form not found")
    res_dict = result.to_mongo().to_dict()
    res_dict['_id'] = str(res_dict['_id'])
    return res_dict