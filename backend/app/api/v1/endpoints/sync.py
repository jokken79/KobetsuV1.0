"""
Sync API Endpoints - Sincronización desde Archivos de Red

Endpoints para sincronizar empleados y fábricas desde los archivos maestros en red.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Optional

from app.core.database import get_db
from app.services.sync_service import sync_from_network

router = APIRouter()


# ========================================
# Sincronización Manual
# ========================================

@router.post("/employees", response_model=Dict)
def sync_employees_endpoint(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Sincroniza empleados desde Excel en red.

    Lee desde: \\UNS-Kikaku\共有フォルダ\SCTDateBase\【新】社員台帳(UNS)T　2022.04.05～.xlsm
    Hoja: DBGenzaiX (oculta)

    Returns:
        Estadísticas de sincronización
    """
    try:
        print("🔄 API: Sincronización de empleados solicitada")
        result = sync_from_network(db, sync_type='employees')
        return result

    except FileNotFoundError as e:
        print(f"❌ Archivo no encontrado: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Archivo no encontrado en red: {str(e)}"
        )
    except Exception as e:
        print(f"❌ Error en sincronización: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error en sincronización de empleados: {str(e)}"
        )


@router.post("/factories", response_model=Dict)
def sync_factories_endpoint(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Sincroniza fábricas desde JSON en red.

    Lee desde:
    - \\UNS-Kikaku\共有フォルダ\SCTDateBase\factories_index.json
    - \\UNS-Kikaku\共有フォルダ\SCTDateBase\factories\*

    Returns:
        Estadísticas de sincronización
    """
    try:
        print("🔄 API: Sincronización de fábricas solicitada")
        result = sync_from_network(db, sync_type='factories')
        return result

    except FileNotFoundError as e:
        print(f"❌ Archivo no encontrado: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Archivo no encontrado en red: {str(e)}"
        )
    except Exception as e:
        print(f"❌ Error en sincronización: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error en sincronización de fábricas: {str(e)}"
        )


@router.post("/all", response_model=Dict)
def sync_all_endpoint(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Sincroniza empleados y fábricas.

    Sincroniza ambos archivos maestros:
    1. Fábricas desde JSON
    2. Empleados desde Excel

    Returns:
        Estadísticas de ambas sincronizaciones
    """
    try:
        print("🔄 API: Sincronización completa solicitada")
        result = sync_from_network(db, sync_type='all')
        return result

    except FileNotFoundError as e:
        print(f"❌ Archivo no encontrado: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Archivo no encontrado en red: {str(e)}"
        )
    except Exception as e:
        print(f"❌ Error en sincronización: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error en sincronización completa: {str(e)}"
        )


# ========================================
# Estado de Sincronización
# ========================================

@router.get("/status", response_model=Dict)
def get_sync_status(db: Session = Depends(get_db)):
    """
    Obtiene el estado actual de los datos.

    Returns:
        Contadores de empleados, fábricas, y última actualización
    """
    from app.models.employee import Employee
    from app.models.factory import Factory, FactoryLine

    try:
        employee_count = db.query(Employee).count()
        employee_active = db.query(Employee).filter_by(status='active').count()

        factory_count = db.query(Factory).count()
        line_count = db.query(FactoryLine).count()

        return {
            'employees': {
                'total': employee_count,
                'active': employee_active,
                'resigned': employee_count - employee_active
            },
            'factories': {
                'total': factory_count,
                'lines': line_count
            },
            'sync_available': True
        }

    except Exception as e:
        print(f"❌ Error obteniendo estado: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo estado: {str(e)}"
        )
