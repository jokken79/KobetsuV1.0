"""
Sync Service - Sincronización con Archivos de Red

Sincroniza datos desde:
1. Excel de empleados: \\UNS-Kikaku\共有フォルダ\SCTDateBase\【新】社員台帳(UNS)T　2022.04.05～.xlsm
2. JSON de fábricas: \\UNS-Kikaku\共有フォルダ\SCTDateBase\factories_index.json

Este servicio mantiene la base de datos sincronizada con los archivos maestros en la red.
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
from decimal import Decimal

import openpyxl
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.employee import Employee
from app.models.factory import Factory, FactoryLine


class SyncService:
    """
    Servicio de sincronización con archivos de red.

    Responsabilidades:
    - Leer Excel de empleados (hoja DBGenzaiX oculta)
    - Leer JSON de fábricas
    - Sincronizar datos con PostgreSQL
    - Manejar conflictos y actualizaciones
    """

    # Rutas en red (configurables via variables de entorno)
    # Para testing local, puedes montar una carpeta:
    # docker-compose: volumes: - "C:/path/to/local/SCTDateBase:/network_data"
    # y luego: SYNC_DATA_PATH=/network_data
    NETWORK_BASE = os.environ.get(
        'SYNC_DATA_PATH',
        r"\\UNS-Kikaku\共有フォルダ\SCTDateBase"
    )
    EMPLOYEES_EXCEL = r"【新】社員台帳(UNS)T　2022.04.05～.xlsm"
    FACTORIES_INDEX = "factories_index.json"
    FACTORIES_DIR = os.environ.get('FACTORIES_DIR', 'config/factories')

    def __init__(self, db: Session):
        self.db = db
        self.stats = {
            'employees': {'total': 0, 'created': 0, 'updated': 0, 'errors': []},
            'factories': {'total': 0, 'created': 0, 'updated': 0, 'errors': []}
        }

    # ========================================
    # EMPLEADOS - Sincronización desde Excel
    # ========================================

    def sync_employees(self) -> Dict:
        """
        Sincroniza empleados desde Excel en red.

        Lee la hoja DBGenzaiX (oculta) del Excel maestro de empleados.
        """
        print("🔄 Iniciando sincronización de empleados...")

        try:
            excel_path = os.path.join(self.NETWORK_BASE, self.EMPLOYEES_EXCEL)

            # Verificar que el archivo existe
            if not os.path.exists(excel_path):
                raise FileNotFoundError(f"No se encontró el archivo: {excel_path}")

            print(f"📂 Leyendo archivo: {excel_path}")

            # Cargar workbook
            wb = openpyxl.load_workbook(excel_path, data_only=True, read_only=True)

            # Verificar que la hoja existe
            if 'DBGenzaiX' not in wb.sheetnames:
                raise ValueError("No se encontró la hoja 'DBGenzaiX' en el Excel")

            ws = wb['DBGenzaiX']
            print(f"✅ Hoja DBGenzaiX encontrada")

            # Procesar empleados
            self._process_employees_sheet(ws)

            wb.close()

            print(f"✅ Sincronización de empleados completada:")
            print(f"  📊 Total procesado: {self.stats['employees']['total']}")
            print(f"  ➕ Creados: {self.stats['employees']['created']}")
            print(f"  🔄 Actualizados: {self.stats['employees']['updated']}")
            print(f"  ❌ Errores: {len(self.stats['employees']['errors'])}")

            return self.stats['employees']

        except Exception as e:
            print(f"❌ Error en sincronización de empleados: {str(e)}")
            self.stats['employees']['errors'].append({
                'type': 'general',
                'message': str(e)
            })
            raise

    def _process_employees_sheet(self, ws):
        """Procesa la hoja DBGenzaiX y sincroniza empleados."""

        # Leer headers para mapear columnas
        headers = [cell.value for cell in list(ws.rows)[0]]
        print(f"📋 Columnas encontradas: {len(headers)}")

        # Mapeo de columnas (ajustar según estructura real)
        col_map = self._get_employee_column_mapping(headers)

        # Procesar cada fila (desde fila 2)
        for row_num, row in enumerate(list(ws.rows)[1:], start=2):
            self.stats['employees']['total'] += 1

            try:
                employee_data = self._extract_employee_data(row, col_map)

                # Validar datos mínimos
                if not employee_data.get('employee_number') or not employee_data.get('full_name_kanji'):
                    print(f"⏭️ Fila {row_num}: Datos insuficientes, omitiendo")
                    continue

                # Buscar empleado existente
                employee = self.db.query(Employee).filter_by(
                    employee_number=employee_data['employee_number']
                ).first()

                if employee:
                    # Actualizar empleado existente
                    self._update_employee(employee, employee_data)
                    self.stats['employees']['updated'] += 1
                    print(f"🔄 Actualizado: {employee_data['employee_number']}")
                else:
                    # Crear nuevo empleado
                    employee = Employee(**employee_data)
                    self.db.add(employee)
                    self.stats['employees']['created'] += 1
                    print(f"➕ Creado: {employee_data['employee_number']}")

                # Commit cada 100 registros
                if self.stats['employees']['total'] % 100 == 0:
                    self.db.commit()
                    print(f"  💾 Commit: {self.stats['employees']['total']} procesados...")

            except Exception as e:
                error_msg = f"Fila {row_num}: {str(e)}"
                self.stats['employees']['errors'].append({
                    'row': row_num,
                    'message': str(e)
                })
                print(f"⚠️ {error_msg}")
                # Rollback para limpiar el error y continuar
                self.db.rollback()
                continue

        # Commit final
        try:
            self.db.commit()
        except Exception as e:
            print(f"⚠️ Error en commit final: {str(e)}")
            self.db.rollback()
            raise

    def _get_employee_column_mapping(self, headers: List) -> Dict:
        """
        Mapea headers del Excel a nombres de campos.

        Estructura esperada de DBGenzaiX:
        0: 現在 (Estado actual)
        1: 社員№
        2: 派遣先ID
        3: 派遣先
        4: 配属先
        5: 配属ライン
        6: 仕事内容
        7: 氏名
        8: カナ
        9: 性別
        10: 国籍
        11: 生年月日
        12: 年齢
        13: 時給
        ...
        """
        # Mapeo básico por índice
        return {
            'status_raw': 0,
            'employee_number': 1,
            'company_name': 3,
            'department': 4,
            'line_name': 5,
            'full_name_kanji': 7,
            'full_name_kana': 8,
            'gender': 9,
            'nationality': 10,
            'date_of_birth': 11,
            'age': 12,
            'hourly_rate': 13,
            # Añadir más según necesites
        }

    def _extract_employee_data(self, row, col_map: Dict) -> Dict:
        """Extrae datos de una fila del Excel."""

        # Función helper para obtener valor de celda
        def get_cell(index):
            if index < len(row):
                return row[index].value
            return None

        # Estado
        status_raw = get_cell(col_map['status_raw'])
        status = 'resigned' if status_raw == '退社' else 'active'

        # Número de empleado
        employee_number = get_cell(col_map['employee_number'])
        if employee_number:
            employee_number = str(employee_number).strip()

        # Fecha de nacimiento
        dob = get_cell(col_map['date_of_birth'])
        if isinstance(dob, datetime):
            dob = dob.date()
        elif isinstance(dob, str):
            try:
                dob = datetime.strptime(dob, '%Y-%m-%d').date()
            except:
                dob = None

        # Tarifa horaria
        hourly_rate = get_cell(col_map['hourly_rate'])
        if hourly_rate:
            try:
                hourly_rate = Decimal(str(hourly_rate))
            except:
                hourly_rate = None

        # Helper para convertir valores a string o None (evitar 0 como entero)
        def to_str_or_none(value):
            if value is None or value == '' or value == 0:
                return None
            return str(value)

        return {
            'employee_number': employee_number,
            'full_name_kanji': to_str_or_none(get_cell(col_map['full_name_kanji'])),
            'full_name_kana': to_str_or_none(get_cell(col_map['full_name_kana'])),
            'gender': to_str_or_none(get_cell(col_map['gender'])),
            'nationality': to_str_or_none(get_cell(col_map['nationality'])) or 'ベトナム',
            'date_of_birth': dob,
            'age': get_cell(col_map['age']),
            'status': status,
            'hourly_rate': hourly_rate,
            'company_name': to_str_or_none(get_cell(col_map['company_name'])),
            'department': to_str_or_none(get_cell(col_map['department'])),
            'line_name': to_str_or_none(get_cell(col_map['line_name'])),
            # Fecha de contratación (requerida) - usar fecha actual si no existe
            'hire_date': date.today()  # Ajustar si hay columna específica
        }

    def _update_employee(self, employee: Employee, data: Dict):
        """Actualiza campos de empleado existente."""
        for key, value in data.items():
            if hasattr(employee, key) and value is not None:
                setattr(employee, key, value)

    # ========================================
    # FÁBRICAS - Sincronización desde JSON
    # ========================================

    def sync_factories(self) -> Dict:
        """
        Sincroniza fábricas desde JSON en red.

        Lee factories_index.json que contiene el índice de todas las fábricas.
        """
        print("🔄 Iniciando sincronización de fábricas...")

        try:
            index_path = os.path.join(self.NETWORK_BASE, self.FACTORIES_INDEX)

            # Verificar que el archivo existe
            if not os.path.exists(index_path):
                raise FileNotFoundError(f"No se encontró el archivo: {index_path}")

            print(f"📂 Leyendo archivo: {index_path}")

            # Cargar JSON
            with open(index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)

            total_factories = index_data.get('total_factories', 0)
            factories_list = index_data.get('factories', [])

            print(f"✅ Índice cargado: {total_factories} fábricas")

            # Procesar cada fábrica
            for factory_data in factories_list:
                self.stats['factories']['total'] += 1

                try:
                    self._process_factory(factory_data)
                except Exception as e:
                    self.stats['factories']['errors'].append({
                        'factory_id': factory_data.get('factory_id'),
                        'message': str(e)
                    })
                    print(f"⚠️ Error procesando fábrica: {str(e)}")
                    continue

            self.db.commit()

            print(f"✅ Sincronización de fábricas completada:")
            print(f"  📊 Total procesado: {self.stats['factories']['total']}")
            print(f"  ➕ Creadas: {self.stats['factories']['created']}")
            print(f"  🔄 Actualizadas: {self.stats['factories']['updated']}")
            print(f"  ❌ Errores: {len(self.stats['factories']['errors'])}")

            return self.stats['factories']

        except Exception as e:
            print(f"❌ Error en sincronización de fábricas: {str(e)}")
            self.stats['factories']['errors'].append({
                'type': 'general',
                'message': str(e)
            })
            raise

    def _process_factory(self, data: Dict):
        """
        Procesa una entrada de fábrica del JSON.

        Estructura:
        {
            "factory_id": "加藤木材工業株式会社__本社工場",
            "client_company": "加藤木材工業株式会社",
            "plant_name": "本社工場",
            "department": "生産1部",
            "line": "2課",
            "hourly_rate": 1700.0
        }
        """
        company_name = data.get('client_company')
        plant_name = data.get('plant_name')
        department = data.get('department')
        line = data.get('line')
        hourly_rate = data.get('hourly_rate', 0)

        if not company_name or not plant_name:
            print(f"⏭️ Datos insuficientes en factory_id: {data.get('factory_id')}")
            return

        # Generar factory_id único: "company_name__plant_name"
        factory_id = f"{company_name}__{plant_name}"

        # Buscar Factory por factory_id único
        factory = self.db.query(Factory).filter_by(
            factory_id=factory_id
        ).first()

        if not factory:
            # Crear nueva Factory
            factory = Factory(
                factory_id=factory_id,
                company_name=company_name,
                plant_name=plant_name,
                is_active=True
            )
            self.db.add(factory)
            self.db.flush()  # Para obtener el ID
            print(f"➕ Factory creada: {factory_id}")

        # Buscar o crear FactoryLine
        factory_line = self.db.query(FactoryLine).filter_by(
            factory_id=factory.id,
            department=department,
            line_name=line
        ).first()

        if factory_line:
            # Actualizar tarifa si cambió
            if factory_line.hourly_rate != Decimal(str(hourly_rate)):
                factory_line.hourly_rate = Decimal(str(hourly_rate))
                self.stats['factories']['updated'] += 1
                print(f"🔄 Line actualizada: {line} - ¥{hourly_rate}")
        else:
            # Crear nueva FactoryLine
            factory_line = FactoryLine(
                factory_id=factory.id,
                department=department,
                line_name=line,
                hourly_rate=Decimal(str(hourly_rate)),
                is_active=True
            )
            self.db.add(factory_line)
            self.stats['factories']['created'] += 1
            print(f"➕ Line creada: {department} - {line}")

    # ========================================
    # SINCRONIZACIÓN DETALLADA DE FÁBRICAS
    # ========================================

    def sync_factories_detailed(self) -> Dict:
        """
        Sincroniza fábricas desde archivos JSON individuales con información completa.

        Lee todos los archivos JSON en config/factories/ que contienen:
        - Información completa de la empresa
        - Datos de la planta/工場
        - Configuración de horarios y calendario
        - Términos de pago
        - Información del supervisor y responsables

        Returns:
            Dict con estadísticas de sincronización
        """
        print("🔄 Iniciando sincronización detallada de fábricas...")

        try:
            factories_dir = os.path.join(self.NETWORK_BASE, self.FACTORIES_DIR)

            # Verificar que el directorio existe
            if not os.path.exists(factories_dir):
                raise FileNotFoundError(f"No se encontró el directorio: {factories_dir}")

            print(f"📂 Leyendo directorio: {factories_dir}")

            # Listar todos los archivos JSON (excluir backup y mapping)
            json_files = [
                f for f in os.listdir(factories_dir)
                if f.endswith('.json') and f != 'factory_id_mapping.json'
            ]

            print(f"✅ Encontrados {len(json_files)} archivos JSON de fábricas")

            # Procesar cada archivo
            for json_file in json_files:
                self.stats['factories']['total'] += 1
                file_path = os.path.join(factories_dir, json_file)

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        factory_data = json.load(f)

                    self._process_factory_detailed(factory_data)

                except Exception as e:
                    error_msg = f"Error en {json_file}: {str(e)}"
                    self.stats['factories']['errors'].append({
                        'file': json_file,
                        'message': str(e)
                    })
                    print(f"⚠️ {error_msg}")
                    self.db.rollback()
                    continue

            self.db.commit()

            print(f"✅ Sincronización detallada de fábricas completada:")
            print(f"  📊 Total procesado: {self.stats['factories']['total']}")
            print(f"  ➕ Creadas: {self.stats['factories']['created']}")
            print(f"  🔄 Actualizadas: {self.stats['factories']['updated']}")
            print(f"  ❌ Errores: {len(self.stats['factories']['errors'])}")

            return self.stats['factories']

        except Exception as e:
            print(f"❌ Error en sincronización detallada de fábricas: {str(e)}")
            self.stats['factories']['errors'].append({
                'type': 'general',
                'message': str(e)
            })
            raise

    def _process_factory_detailed(self, data: Dict):
        """
        Procesa un archivo JSON de fábrica completo.

        Estructura esperada:
        {
            "factory_id": "会社名_工場名",
            "client_company": {...},
            "plant": {...},
            "assignment": {...},
            "job": {...},
            "schedule": {...},
            "payment": {...},
            "agreement": {...},
            "dispatch_company": {...}
        }
        """
        factory_id = data.get('factory_id')

        if not factory_id:
            print(f"⏭️ factory_id faltante en datos")
            return

        # Extraer información de la empresa cliente
        client_company = data.get('client_company', {})
        company_name = client_company.get('name')

        # Extraer información de la planta
        plant = data.get('plant', {})
        plant_name = plant.get('name')

        if not company_name or not plant_name:
            print(f"⏭️ Datos insuficientes para {factory_id}")
            return

        # Buscar o crear Factory
        factory = self.db.query(Factory).filter_by(
            factory_id=factory_id
        ).first()

        is_new = factory is None

        if is_new:
            factory = Factory(
                factory_id=factory_id,
                company_name=company_name,
                plant_name=plant_name
            )
            self.db.add(factory)
            print(f"➕ Factory creada: {factory_id}")
        else:
            print(f"🔄 Actualizando factory: {factory_id}")

        # Actualizar información de la empresa cliente
        factory.company_address = client_company.get('address')
        factory.company_phone = client_company.get('phone')

        responsible = client_company.get('responsible_person', {})
        factory.client_responsible_department = responsible.get('department')
        factory.client_responsible_name = responsible.get('name')
        factory.client_responsible_phone = responsible.get('phone')

        complaint_handler = client_company.get('complaint_handler', {})
        factory.client_complaint_department = complaint_handler.get('department')
        factory.client_complaint_name = complaint_handler.get('name')
        factory.client_complaint_phone = complaint_handler.get('phone')

        # Actualizar información de la planta
        factory.plant_address = plant.get('address')
        factory.plant_phone = plant.get('phone')

        # Actualizar información del派遣元 (dispatch company)
        dispatch_company = data.get('dispatch_company', {})
        dispatch_responsible = dispatch_company.get('responsible_person', {})
        factory.dispatch_responsible_department = dispatch_responsible.get('department')
        factory.dispatch_responsible_name = dispatch_responsible.get('name')
        factory.dispatch_responsible_phone = dispatch_responsible.get('phone')

        dispatch_complaint = dispatch_company.get('complaint_handler', {})
        factory.dispatch_complaint_department = dispatch_complaint.get('department')
        factory.dispatch_complaint_name = dispatch_complaint.get('name')
        factory.dispatch_complaint_phone = dispatch_complaint.get('phone')

        # Actualizar información de horarios
        schedule = data.get('schedule', {})
        factory.work_hours_description = schedule.get('work_hours')
        factory.break_time_description = schedule.get('break_time')
        factory.calendar_description = schedule.get('calendar')
        factory.overtime_description = schedule.get('overtime_labor')
        factory.holiday_work_description = schedule.get('non_work_day_labor')

        # Parsear conflict_date (抵触日)
        if schedule.get('conflict_date'):
            try:
                conflict_date_str = schedule.get('conflict_date')
                if isinstance(conflict_date_str, str):
                    factory.conflict_date = datetime.strptime(
                        conflict_date_str.split()[0], '%Y-%m-%d'
                    ).date()
            except Exception as e:
                print(f"⚠️ Error parseando conflict_date: {e}")

        # Time unit
        if schedule.get('time_unit'):
            try:
                factory.time_unit_minutes = Decimal(str(schedule.get('time_unit')))
            except:
                pass

        # Actualizar términos de pago
        payment = data.get('payment', {})
        factory.closing_date = payment.get('closing_date')
        factory.payment_date = payment.get('payment_date')
        factory.bank_account = payment.get('bank_account')
        factory.worker_closing_date = payment.get('worker_closing_date')
        factory.worker_payment_date = payment.get('worker_payment_date')
        factory.worker_calendar = payment.get('worker_calendar')

        # Actualizar información del acuerdo
        agreement = data.get('agreement', {})
        if agreement.get('period'):
            try:
                period_str = agreement.get('period')
                if isinstance(period_str, str):
                    factory.agreement_period = datetime.strptime(
                        period_str.split()[0], '%Y-%m-%d'
                    ).date()
            except Exception as e:
                print(f"⚠️ Error parseando agreement_period: {e}")

        factory.agreement_explainer = agreement.get('explainer')
        factory.is_active = True

        self.db.flush()  # Asegurar que tenemos el ID de la factory

        # Procesar línea/departamento
        assignment = data.get('assignment', {})
        job = data.get('job', {})

        department = assignment.get('department')
        line_name = assignment.get('line')

        if department or line_name:
            # Buscar o crear FactoryLine
            factory_line = self.db.query(FactoryLine).filter_by(
                factory_id=factory.id,
                department=department,
                line_name=line_name
            ).first()

            if not factory_line:
                factory_line = FactoryLine(
                    factory_id=factory.id,
                    department=department,
                    line_name=line_name
                )
                self.db.add(factory_line)
                print(f"  ➕ Line creada: {department} - {line_name}")

            # Actualizar información del supervisor
            supervisor = assignment.get('supervisor', {})
            factory_line.supervisor_department = supervisor.get('department')
            factory_line.supervisor_name = supervisor.get('name')
            factory_line.supervisor_phone = supervisor.get('phone')

            # Actualizar información del trabajo
            factory_line.job_description = job.get('description')
            factory_line.job_description_detail = job.get('description2')

            if job.get('hourly_rate'):
                try:
                    factory_line.hourly_rate = Decimal(str(job.get('hourly_rate')))
                except:
                    pass

            factory_line.is_active = True

        if is_new:
            self.stats['factories']['created'] += 1
        else:
            self.stats['factories']['updated'] += 1

    # ========================================
    # SINCRONIZACIÓN COMPLETA
    # ========================================

    def sync_all(self) -> Dict:
        """
        Sincroniza empleados y fábricas usando sincronización detallada.

        Returns:
            Dict con estadísticas de ambas sincronizaciones
        """
        print("="*60)
        print("🚀 SINCRONIZACIÓN COMPLETA INICIADA")
        print("="*60)

        start_time = datetime.now()

        try:
            # Sincronizar fábricas primero con información detallada
            factories_stats = self.sync_factories_detailed()

            # Luego sincronizar empleados
            employees_stats = self.sync_employees()

            elapsed = (datetime.now() - start_time).total_seconds()

            print("="*60)
            print(f"✅ SINCRONIZACIÓN COMPLETADA EN {elapsed:.2f}s")
            print("="*60)

            return {
                'success': True,
                'employees': employees_stats,
                'factories': factories_stats,
                'elapsed_seconds': elapsed
            }

        except Exception as e:
            print(f"❌ Error en sincronización completa: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'employees': self.stats['employees'],
                'factories': self.stats['factories']
            }


# ========================================
# Función helper para uso en endpoints
# ========================================

def sync_from_network(db: Session, sync_type: str = 'all') -> Dict:
    """
    Helper function para sincronizar desde archivos de red.

    Args:
        db: SQLAlchemy session
        sync_type: 'employees', 'factories', o 'all'

    Returns:
        Dict con estadísticas de sincronización
    """
    service = SyncService(db)

    if sync_type == 'employees':
        return {'employees': service.sync_employees()}
    elif sync_type == 'factories':
        return {'factories': service.sync_factories_detailed()}
    else:  # 'all'
        return service.sync_all()
