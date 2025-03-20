#Librerias y framework
from flask import Flask, request, render_template, redirect, url_for, session, make_response, jsonify, send_file,flash
import pandas as pd
import psycopg2
import random
import string
import json
import traceback
from psycopg2.extras import Json
import datetime
from flask.json.provider import DefaultJSONProvider
import smtplib
import ssl
from email.message import EmailMessage
import os
import re
from datetime import datetime, timedelta, date, time
import holidays
from dateutil.relativedelta import relativedelta
from io import BytesIO
import base64
import locale
locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8') 


app = Flask(__name__)
app.secret_key = 'Contreseña'

def generar_contrasena(longitud=12):
    # Asegurar que siempre empiece con TEMP_ y tenga la longitud correcta
    temp_part = 'TEMP_'
    random_part = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(longitud - len(temp_part)))
    return temp_part + random_part

class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, datetime):  
            return obj.isoformat()  # Convierte datetime a string
        if isinstance(obj, date):  
            return obj.isoformat()  # Convierte date a string
        if isinstance(obj, time):  # Agrega soporte para objetos time
            return obj.isoformat()
        return super().default(obj)
    

app.json_provider_class = CustomJSONProvider
app.json = app.json_provider_class(app)

#Conexión a la base de datos
host='localhost'
database='postgres2'
user='postgres'
password='024689'

# Conexión con el login
@app.route('/', methods=['GET', 'POST'])
def login():
    # Redirigir si ya hay sesión activa
    if 'usuario' in session:
        if session.get('password_temp'):
            return redirect(url_for('cambiar_contraseña'))
        return redirect(url_for('dashboard_admin' if session.get('es_admin') else 'dashboard_empleados'))
    
    # Manejar POST (envío de credenciales)
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        contrasena = request.form.get('contrasena', '').strip()
        
        if not nombre or not contrasena:
            return render_template('login.html', error="Campos vacíos")
            
        conn = None
        cursor = None
        try:
            # 1. Conexión a la base de datos
            conn = psycopg2.connect(host=host, database=database, user=user, password=password)
            cursor = conn.cursor()

            # 2. Verificar ADMIN primero
            cursor.execute("""
                SELECT id_usuario, contrasena 
                FROM USUARIO 
                WHERE nombre = %s AND contrasena = %s
            """, (nombre, contrasena))
            admin = cursor.fetchone()
            
            if admin:
                password_temp = admin[1].startswith('TEMP_')
                # Configurar sesión para admin
                session.update({
                    'usuario': nombre,
                    'id_uem': admin[0],
                    'es_admin': True,
                    'password_temp': password_temp
                })
                
                return redirect(url_for('cambiar_contraseña')) if password_temp else redirect(url_for('dashboard_admin'))

            # 3. Si no es admin, verificar COLABORADOR
            cursor.execute("""
                SELECT id_uem, contrasena 
                FROM colaboradores 
                WHERE usuario = %s AND contrasena = %s
            """, (nombre, contrasena))
            empleado = cursor.fetchone()
            
            if empleado:
                password_temp = empleado[1].startswith('TEMP_')
                # Configurar sesión para empleado
                session.update({
                    'usuario': nombre,
                    'id_uem': empleado[0],
                    'es_admin': False,
                    'password_temp': password_temp
                })
                
                return redirect(url_for('cambiar_contraseña')) if password_temp else redirect(url_for('dashboard_empleados'))

            # 4. Si no coincide con ningún usuario
            return render_template('login.html', error="Credenciales incorrectas")

        except psycopg2.OperationalError as e:
            print(f"Error de conexión: {str(e)}")
            return render_template('login.html', error="Error de conexión a la base de datos")
            
        except Exception as e:
            print(f"Error inesperado: {str(e)}")
            return render_template('login.html', error="Error interno del servidor")
            
        finally:
            # 5. Limpieza garantizada de recursos
            if cursor: cursor.close()
            if conn: conn.close()

    # GET: Mostrar página de login
    response = make_response(render_template('login.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

#Cerrar sesión
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    session.pop('es_admin', None)
    return redirect(url_for('login'))

#Página principal del administrador
@app.route('/dashboard_admin')
def dashboard_admin():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    if session.get('password_temp'):
        return redirect(url_for('cambiar_contraseña'))
    return render_template('Admin/dashboard_admin.html', nombre=session['usuario'])


# Configuración de correo emisor (Ionos)
EMAIL_EMISOR = "yaeylin.irais.garcia@yotoss.com"
EMAIL_CONTRA = "Y43_1r4is&2024"

# Función para enviar correo solo a dominios permitidos
def send_email(user, password, receptor):
    # Expresión regular para aceptar SOLO @yotoss.com y @padice.org
    if not re.match(r"^[a-zA-Z0-9._%+-]+@(yotoss\.com|padice\.org)$", receptor):
        print("❌ Error: Solo se pueden enviar correos a @yotoss.com o @padice.org")
        return False  # 🔴 DETIENE el envío inmediatamente

    asunto = "Credenciales de acceso"
    cuerpo = f"""
    Tu usuario es: {user}
    Tu contraseña es: {password}

    "Por seguridad, esta contraseña es temporal. Cámbiala al acceder a tu cuenta para mantener la confidencialidad de tu información."
    Saludos.
    """

    em = EmailMessage()
    em["From"] = EMAIL_EMISOR
    em["To"] = receptor
    em["Subject"] = asunto
    em.set_content(cuerpo)

    contexto = ssl.create_default_context()

    try:
        with smtplib.SMTP_SSL("smtp.ionos.com", 465, context=contexto) as smtp:
            smtp.login(EMAIL_EMISOR, EMAIL_CONTRA)
            smtp.sendmail(EMAIL_EMISOR, receptor, em.as_string())
        print("✅ Correo enviado correctamente.")
        return True
    except Exception as e:
        print(f"⚠️ Error al enviar el correo: {e}")
        return False

# Añadir empleados (Admin) 
@app.route('/añadir_empleados', methods=['GET', 'POST'])
def añadir_empleados():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            # Determinar si la petición es JSON o envío tradicional
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form

            # Validar y obtener la lista de horarios
            if request.is_json:
                if not data.get('horarios'):
                    raise ValueError("⚠️ ¡Debes agregar al menos un horario!")
                horarios = data['horarios']
            else:
                if not data.get('horarios_data'):
                    raise ValueError("⚠️ ¡Debes agregar al menos un horario!")
                try:
                    horarios = json.loads(data['horarios_data'])
                except json.JSONDecodeError as e:
                    raise ValueError(f"Formato de horarios inválido: {str(e)}")
            
            if not isinstance(horarios, list) or len(horarios) == 0:
                raise ValueError("⚠️ La lista de horarios está vacía")
            
            # Usar la contraseña que envía el formulario (ya con "TEMP_")
            contrasena_temporal = data.get('contrasena')
            if not contrasena_temporal:
                # Si por alguna razón no se envía, la generamos en el servidor
                contrasena_temporal = generar_contrasena()

            with psycopg2.connect(
                dbname="postgres2",
                user="postgres",
                password="024689",
                host="localhost"
            ) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO colaboradores (
                            nombre_completo, fecha_nacimiento, direccion, 
                            telefono, email, departamento, 
                            fecha_contratacion, usuario, contrasena
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id_uem
                    """, (
                        data['nombre_completo'].strip(),
                        data['fecha_nacimiento'],
                        data['direccion'],
                        data['telefono'],
                        data['email'],
                        data['departamento'],
                        data['fecha_contratacion'],
                        data['usuario'],
                        contrasena_temporal
                    ))
                    id_uem = cur.fetchone()[0]

                    for horario in horarios:
                        cur.execute("""
                            INSERT INTO horarios (
                                id_uem_fk, horario_entrada, 
                                horario_salida, dias_trabajo
                            ) VALUES (%s, %s, %s, %s)
                        """, (
                            id_uem,
                            horario['horario_entrada'],
                            horario['horario_salida'],
                            psycopg2.extras.Json(horario['dias'])
                        ))
                    
                    conn.commit()

            # Enviar correo con las credenciales temporales
            if send_email(data['usuario'], contrasena_temporal, data['email']):
                return jsonify({'success': True, 'message': 'Empleado agregado y correo enviado correctamente'})
            else:
                return jsonify({'success': True, 'message': 'Empleado agregado, pero hubo un error al enviar el correo'})

        except Exception as e:
            error_msg = f"Error al guardar: {str(e)}"
            print(error_msg)
            traceback.print_exc()
            return jsonify({'success': False, 'error': error_msg}), 500

    # GET: Mostrar formulario y tabla
    try:
        with psycopg2.connect(
            dbname="postgres2",
            user="postgres",
            password="024689",
            host="localhost"
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        c.id_uem,
                        c.nombre_completo,
                        c.fecha_nacimiento,
                        c.direccion,
                        c.telefono,
                        c.email,
                        c.departamento,
                        c.fecha_contratacion,
                        c.usuario,
                        c.contrasena,
                        COALESCE(ARRAY_AGG(h.horario_entrada), '{}'),
                        COALESCE(ARRAY_AGG(h.horario_salida), '{}'),
                        COALESCE(json_agg(h.dias_trabajo), '[]'::json)
                    FROM colaboradores c
                    LEFT JOIN horarios h ON c.id_uem = h.id_uem_fk
                    GROUP BY c.id_uem
                    ORDER BY c.nombre_completo ASC
                """)
                colaboradores = []
                for row in cur.fetchall():
                    row = list(row)
                    row[12] = json.loads(row[12]) if isinstance(row[12], str) else row[12]
                    colaboradores.append(row)

        return render_template(
            'Admin/añadir_empleados.html',
            nombre=session['usuario'],
            colaboradores=colaboradores
        )

    except Exception as e:
        print(f"Error: {str(e)}")
        return render_template('Admin/añadir_empleados.html', error=str(e))


#Sistema de asistencias (Admin) 
@app.route('/asistencias')
def asistencias():
    return render_template('Admin/asistencias.html')

def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        database='postgres2',
        user='postgres',
        password='024689'
    )

# Ruta para historial de empleados (Admin)
@app.route('/historial_empleados_admin')
def historial_empleados_admin():
    if not session.get('es_admin'):
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Obtener parámetros de filtrado desde la URL
        filter_ids = request.args.get('filter_ids', '')
        filter_types = request.args.get('filter_types', '')
        filter_status = request.args.get('filter_status', '')

        # Procesar los filtros recibidos: convertimos a enteros y mayúsculas cuando sea necesario
        selected_ids = [int(x) for x in filter_ids.split(',') if x.strip().isdigit()]
        selected_types = [t.strip().upper() for t in filter_types.split(',') if t.strip()]
        selected_status = [e.strip().upper() for e in filter_status.split(',') if e.strip()]

        # Listas fijas de valores permitidos
        TIPOS_PERMITIDOS = ['PERMISO', 'INCAPACIDAD', 'VACACIONES']
        ESTADOS_PERMITIDOS = ['PENDIENTE', 'APROBADO', 'RECHAZADO']

        # Consulta base
        base_query = """
            SELECT 
                s.id,
                s.fecha_inicio,
                s.fecha_fin,
                s.tipo,
                s.estado,
                COALESCE(p.comentario, i.comentario, '---') AS descripcion,
                c.nombre_completo AS nombre_usuario
            FROM solicitudes s
            JOIN colaboradores c ON s.id_uem = c.id_uem
            LEFT JOIN permisos p ON s.id = p.solicitud_id
            LEFT JOIN incapacidades i ON s.id = i.solicitud_id
            WHERE 1=1
        """

        params = []
        conditions = []

        # Filtro por usuarios: convertimos la lista a una tupla y usamos IN
        if selected_ids:
            conditions.append("c.id_uem IN %s")
            params.append(tuple(selected_ids))

        # Filtro por tipos: mantenemos el filtro usando ANY para el arreglo de texto
        selected_types = [t for t in selected_types if t in TIPOS_PERMITIDOS]
        if selected_types:
            conditions.append("s.tipo = ANY(%s::text[])")
            params.append(selected_types)

        # Filtro por estados: similar al filtro de tipos
        selected_status = [e for e in selected_status if e in ESTADOS_PERMITIDOS]
        if selected_status:
            conditions.append("s.estado = ANY(%s::text[])")
            params.append(selected_status)

        # Construir la consulta final
        final_query = base_query
        if conditions:
            final_query += " AND " + " AND ".join(conditions)
        final_query += " ORDER BY s.fecha_inicio DESC"

        # Imprimir en consola para depuración
        print("DEBUG - Query:", final_query)
        print("DEBUG - Params:", params)

        cur.execute(final_query, params)
        solicitudes = cur.fetchall()

        solicitudes_list = [{
            "id": row[0],
            "fecha_inicio": row[1],
            "fecha_fin": row[2],
            "tipo": row[3],
            "estado": row[4],
            "descripcion": row[5],
            "nombre_usuario": row[6]
        } for row in solicitudes]

        # Obtener la lista de empleados para el filtro
        cur.execute("SELECT id_uem, nombre_completo FROM colaboradores ORDER BY nombre_completo")
        empleados = cur.fetchall()

        return render_template("Admin/historial_empleados_admin.html",
                               solicitudes=solicitudes_list,
                               empleados=empleados,
                               tipos=TIPOS_PERMITIDOS,
                               estados=ESTADOS_PERMITIDOS,
                               selected_ids=selected_ids,
                               selected_types=selected_types,
                               selected_status=selected_status)

    except Exception as e:
        print("Error en historial_empleados_admin:", e)
        return f"Error: {str(e)}"
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()



@app.route('/generar_contrasena')
def generar():
    contrasena = generar_contrasena()
    return jsonify({'contrasena': contrasena})

# Gestión de empleados (Admin) 
@app.route('/gestion_empleados')
def gestion_empleados():
    if 'usuario' in session:
        try:
            with psycopg2.connect(
                dbname="postgres2",
                user="postgres",
                password="024689",
                host="localhost"
            ) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            c.id_uem,
                            c.nombre_completo,
                            c.fecha_nacimiento,
                            c.direccion,
                            c.telefono,
                            c.email,
                            c.departamento,
                            c.fecha_contratacion,
                            c.usuario,
                            c.contrasena,
                            COALESCE(ARRAY_AGG(h.horario_entrada), '{}') AS entradas,
                            COALESCE(ARRAY_AGG(h.horario_salida), '{}') AS salidas,
                            COALESCE(json_agg(h.dias_trabajo), '[]'::json) AS dias
                        FROM colaboradores c
                        LEFT JOIN horarios h ON c.id_uem = h.id_uem_fk
                        GROUP BY c.id_uem
                        ORDER BY c.nombre_completo ASC
                    """)
                    colaboradores = []
                    for row in cur.fetchall():
                        row = list(row)
                        row[10] = row[10] if row[10] else []
                        row[11] = row[11] if row[11] else []
                        row[12] = json.loads(row[12]) if row[12] else []
                        colaboradores.append(row)

                    return render_template(
                        'Admin/añadir_empleados.html',
                        nombre=session['usuario'],
                        colaboradores=colaboradores
                    )
        except Exception as e:
            print(f"Error: {str(e)}")
            return render_template('error.html', mensaje="Error al cargar empleados")
    else:
        return redirect(url_for('login'))

# Ruta para eliminar colaborador (Admin) 
@app.route('/eliminar_colaborador/<int:id_uem>', methods=['DELETE'])
def eliminar_colaborador(id_uem):
    try:
        with psycopg2.connect(
            dbname="postgres2",
            user="postgres",
            password="024689",
            host="localhost"
        ) as conn:
            with conn.cursor() as cur:
                conn.autocommit = False
                try:
                    cur.execute("DELETE FROM horarios WHERE id_uem_fk = %s", (id_uem,))
                    print(f"Horarios del colaborador {id_uem} eliminados")
                    cur.execute("DELETE FROM colaboradores WHERE id_uem = %s", (id_uem,))
                    print(f"Colaborador {id_uem} eliminado")
                    conn.commit()
                    return jsonify({
                        'success': True,
                        'message': f'Colaborador {id_uem} eliminado correctamente'
                    }), 200
                except Exception as e:
                    conn.rollback()
                    print(f"Error durante la eliminación: {str(e)}")
                    return jsonify({ 
                        'success': False,
                        'error': str(e),
                        'message': f'Error al eliminar el colaborador {id_uem}'
                    }), 500
    except Exception as e:
        print(f"Error de conexión a la base de datos: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Error de conexión a la base de datos'
        }), 500

# Ruta para obtener datos de un colaborador (ahora con fechas formateadas) (Admin) 
@app.route('/obtener_colaborador/<int:id_uem>')
def obtener_colaborador(id_uem):
    try:
        with psycopg2.connect(
            dbname="postgres2",
            user="postgres",
            password="024689",
            host="localhost"
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id_uem, nombre_completo, fecha_nacimiento, direccion, 
                           telefono, email, departamento, fecha_contratacion, usuario, contrasena
                    FROM colaboradores 
                    WHERE id_uem = %s
                """, (id_uem,))
                colaborador = cur.fetchone()
                if not colaborador:
                    return jsonify({'error': 'No se encontró el colaborador'}), 404

                colaborador_data = {
                    'id_uem': colaborador[0],
                    'nombre_completo': colaborador[1],
                    'fecha_nacimiento': colaborador[2].isoformat() if colaborador[2] else None,
                    'direccion': colaborador[3],
                    'telefono': colaborador[4],
                    'email': colaborador[5],
                    'departamento': colaborador[6],
                    'fecha_contratacion': colaborador[7].isoformat() if colaborador[7] else None,
                    'usuario': colaborador[8],
                    'contrasena': colaborador[9]
                }

                cur.execute("""
                    SELECT horario_entrada, horario_salida, dias_trabajo 
                    FROM horarios 
                    WHERE id_uem_fk = %s
                """, (id_uem,))
                horarios = []
                for row in cur.fetchall():
                    horarios.append({
                        'horario_entrada': row[0],
                        'horario_salida': row[1],
                        'dias': row[2]
                    })
                
        return jsonify({
            'colaborador': colaborador_data,
            'horarios': horarios
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Ruta para actualizar colaborador (Admin) 
@app.route('/actualizar_colaborador/<int:id_uem>', methods=['PUT'])
def actualizar_colaborador(id_uem):
    try:
        data = request.get_json()
        print("Datos recibidos para actualizar (id {}): {}".format(id_uem, data))
        with psycopg2.connect(
            dbname="postgres2",
            user="postgres",
            password="024689",
            host="localhost"
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE colaboradores SET
                        nombre_completo = %s,
                        fecha_nacimiento = %s,
                        direccion = %s,
                        telefono = %s,
                        email = %s,
                        departamento = %s,
                        fecha_contratacion = %s,
                        usuario = %s,
                        contrasena = %s
                    WHERE id_uem = %s
                """, (
                    data.get('nombre_completo'),
                    data.get('fecha_nacimiento'),
                    data.get('direccion'),
                    data.get('telefono'),
                    data.get('email'),
                    data.get('departamento'),
                    data.get('fecha_contratacion'),
                    data.get('usuario'),
                    data.get('contrasena'),
                    id_uem
                ))
                # Eliminar horarios anteriores
                cur.execute("DELETE FROM horarios WHERE id_uem_fk = %s", (id_uem,))
                for horario in data.get('horarios', []):
                    cur.execute("""
                        INSERT INTO horarios (
                            id_uem_fk, horario_entrada, horario_salida, dias_trabajo
                        ) VALUES (%s, %s, %s, %s)
                    """, (
                        id_uem,
                        horario.get('horario_entrada'),
                        horario.get('horario_salida'),
                        Json(horario.get('dias'))
                    ))
                conn.commit()
        print("Actualización exitosa para id_uem:", id_uem)
        return jsonify({'success': True, 'message': 'Actualización exitosa'})
    except Exception as e:
        print("Error en actualizar_colaborador:", str(e))
        return jsonify({'success': False, 'error': str(e)}), 500

# Proteger dashboard
@app.route('/dashboard_empleados')
def dashboard_empleados():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    if session.get('password_temp'):
        return redirect(url_for('cambiar_contraseña'))
    return render_template('Empleados/dashboard_empleados.html', nombre=session['usuario'])

@app.route('/pedirvacaciones', methods=['GET'])
def pedirvacaciones():
    id_uem = session.get('id_uem')
    if not id_uem:
        return jsonify({'error': 'No autenticado'}), 401

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT fecha_contratacion FROM colaboradores WHERE id_uem = %s", (id_uem,))
        resultado = cur.fetchone()
        if not resultado:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        fecha_contratacion = resultado[0]

        delta = relativedelta(datetime.now().date(), fecha_contratacion)
        años_completos = delta.years
        if años_completos < 1:
            return jsonify({'dias_disponibles': 0, 'mensaje': '❌ No tienes días de vacaciones en tu primer año.'})

        dias_vacaciones = 12 + 2 * (años_completos - 1)
        cur.execute("""
            SELECT SUM((fecha_fin - fecha_inicio) :: INTEGER) + COUNT(*)
            FROM solicitudes
            WHERE id_uem = %s AND tipo = 'VACACIONES' AND estado = 'APROBADO'
        """, (id_uem,))
        dias_usados = cur.fetchone()[0] or 0
        dias_restantes = max(dias_vacaciones - dias_usados, 0)
        return jsonify({'dias_disponibles': dias_restantes})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/solicitar_permiso', methods=['POST'])
def solicitar_permiso():
    id_uem = session.get('id_uem')
    if not id_uem:
        flash('Debes iniciar sesión para realizar esta acción.')
        return redirect(url_for('login'))

    tipo = request.form.get('tipo')
    fecha_inicio = request.form.get('fechaInicio')
    fecha_fin = request.form.get('fechaFin')
    comentario = request.form.get('comentario', '').strip()
    archivo = request.files.get('archivo')

    try:
        fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
    except ValueError:
        flash('Formato de fecha inválido.')
        return redirect(url_for('dashboard_empleados'))

    if fecha_fin_dt < fecha_inicio_dt:
        flash('La fecha de fin no puede ser anterior a la de inicio.')
        return redirect(url_for('dashboard_empleados'))

   # Dentro de la función solicitar_permiso()
# Dentro de la ruta /solicitar_permiso
    # Dentro de la ruta /solicitar_permiso
    if tipo in ['PERMISO', 'INCAPACIDAD']:
        # Validar que haya comentario
        if not comentario:
            flash('Debes escribir un comentario.')
            return redirect(url_for('dashboard_empleados'))

        # Validar que haya archivo adjunto
        if not archivo or archivo.filename == '':
            flash('Debes subir un justificante.')
            return redirect(url_for('dashboard_empleados'))

        # Validar tipo MIME y extensión
        mime_permitidos = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf']
        extensiones_permitidas = {'jpg', 'jpeg', 'png', 'pdf'}

        # Obtener extensión del archivo
        filename = archivo.filename.lower()
        extension = filename.rsplit('.', 1)[1] if '.' in filename else ''
        mime_type = archivo.mimetype  # Obtener el tipo MIME

        if mime_type not in mime_permitidos or extension not in extensiones_permitidas:
            flash('❌ Formato no válido. Solo se aceptan JPEG, JPG, PNG o PDF.')
            return redirect(url_for('dashboard_empleados'))



    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if tipo == 'VACACIONES':
            cur.execute("SELECT fecha_contratacion FROM colaboradores WHERE id_uem = %s", (id_uem,))
            resultado = cur.fetchone()
            if not resultado:
                flash('No se encontró la fecha de contratación del usuario.')
                return redirect(url_for('dashboard_empleados'))
            fecha_contratacion = resultado[0]

            delta = relativedelta(datetime.now().date(), fecha_contratacion)
            años_completos = delta.years
            if años_completos < 1:
                flash('❌ No tienes días de vacaciones en tu primer año.')
                return redirect(url_for('dashboard_empleados'))

            dias_vacaciones = 12 + 2 * (años_completos - 1)
            cur.execute("""
                SELECT SUM((fecha_fin - fecha_inicio) :: INTEGER) + COUNT(*)
                FROM solicitudes
                WHERE id_uem = %s AND tipo = 'VACACIONES' AND estado = 'APROBADO'
            """, (id_uem,))
            dias_usados = cur.fetchone()[0] or 0
            dias_restantes = max(dias_vacaciones - dias_usados, 0)

            rango_fechas = [fecha_inicio_dt + timedelta(days=i) for i in range((fecha_fin_dt - fecha_inicio_dt).days + 1)]
            years = list({fecha.year for fecha in rango_fechas})
            mx_holidays = holidays.Mexico(years=years)
            dias_solicitados = sum(1 for fecha in rango_fechas if fecha.weekday() < 5 and fecha not in mx_holidays)

            if dias_solicitados > dias_restantes:
                flash(f'⚠ Días disponibles: {dias_restantes} | Solicitaste: {dias_solicitados}')
                return redirect(url_for('dashboard_empleados'))

        cur.execute("""
            INSERT INTO solicitudes (id_uem, tipo, fecha_inicio, fecha_fin)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (id_uem, tipo, fecha_inicio, fecha_fin))
        solicitud_id = cur.fetchone()[0]

        if tipo == 'PERMISO':
            cur.execute("""
                INSERT INTO permisos (solicitud_id, justificante, comentario)
                VALUES (%s, %s, %s)
            """, (solicitud_id, archivo.read(), comentario))
        elif tipo == 'VACACIONES':
            cur.execute("INSERT INTO vacaciones (solicitud_id) VALUES (%s)", (solicitud_id,))
        elif tipo == 'INCAPACIDAD':
            cur.execute("""
                INSERT INTO incapacidades (solicitud_id, comentario, justificante)
                VALUES (%s, %s, %s)
            """, (solicitud_id, comentario, archivo.read()))

        conn.commit()
        flash('✅ Solicitud enviada correctamente.')
        return redirect(url_for('dashboard_empleados'))

    except Exception as e:
        if conn:
            conn.rollback()
        flash(f'❌ Error: {str(e)}')
        return redirect(url_for('dashboard_empleados'))

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/verestatus_solicitudes')
def veresverestatus_solicitudestatus():
    id_uem = session.get('id_uem')
    if not id_uem:
        return jsonify({"error": "No autorizado"}), 401

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT tipo, estado
            FROM solicitudes
            WHERE id_uem = %s
        """, (id_uem,))
        
        solicitudes = []
        for row in cur.fetchall():
            solicitudes.append({
                "tipo": row[0].strip().upper(),
                "estado": row[1]
            })
            
        return jsonify(solicitudes)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

@app.route('/historial_empleados')
def historial_empleados():
    id_uem = session.get('id_uem')
    if not id_uem:
        return redirect(url_for('login'))
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                to_char(s.fecha_inicio, 'TMMonth YYYY') AS mes_anio,
                s.fecha_inicio,
                s.fecha_fin,
                ((s.fecha_fin - s.fecha_inicio) + 1) AS dias_totales,
                s.tipo,
                s.estado,
                CASE 
                    WHEN s.tipo = 'VACACIONES' THEN '---'
                    WHEN s.tipo = 'PERMISO' THEN p.comentario
                    WHEN s.tipo = 'INCAPACIDAD' THEN i.comentario
                    ELSE '---'
                END AS descripcion,
                c.nombre_completo AS nombre_usuario
            FROM solicitudes s
            LEFT JOIN colaboradores c ON s.id_uem = c.id_uem
            LEFT JOIN permisos p ON s.id = p.solicitud_id
            LEFT JOIN incapacidades i ON s.id = i.solicitud_id
            WHERE s.id_uem = %s
            ORDER BY s.fecha_inicio DESC
        """, (id_uem,))
        solicitudes = cur.fetchall()
        solicitudes_list = []
        for row in solicitudes:
            solicitudes_list.append({
                "mes_anio": row[0],
                "fecha_inicio": row[1].strftime("%d/%m/%Y") if row[1] else "",
                "fecha_fin": row[2].strftime("%d/%m/%Y") if row[2] else "",
                "dias_totales": row[3],
                "tipo": row[4].strip().upper(),
                "estado": row[5],
                "descripcion": row[6],
                "nombre_usuario": row[7]
            })
        return render_template("Empleados/historial_empleados.html", solicitudes=solicitudes_list)
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route('/verestatus')
def ver_estatus():  # ✅
    id_uem = session.get('id_uem')
    if not id_uem:
        return jsonify({"error": "No autorizado"}), 401

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                s.creado_en,
                s.tipo,
                s.estado,
                v.comentario AS comentario_admin
            FROM solicitudes s
            LEFT JOIN validaciones v ON s.id = v.solicitud_id
            WHERE s.id_uem = %s
            ORDER BY s.creado_en DESC
        """, (id_uem,))
        
        solicitudes = []
        for row in cur.fetchall():
            fecha_formateada = row[0].strftime("%d/%m/%Y %H:%M:%S")
            solicitudes.append({
                "creado_en": fecha_formateada,
                "tipo": row[1].strip().upper(),
                "estado": row[2],
                "comentario_admin": row[3] if row[3] else "Sin comentario"  # Si no hay comentario, muestra "Sin comentario"
            })
            
        return jsonify(solicitudes)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/descargar_historial')
def descargar_historial():
    if 'usuario' not in session or session.get('es_admin'):
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Obtener datos del usuario
        cur.execute("SELECT nombre_completo, departamento FROM colaboradores WHERE id_uem = %s", (session['id_uem'],))
        usuario = cur.fetchone()
        
        # 2. Obtener historial (sin estado)
        cur.execute("""
            SELECT 
                to_char(s.fecha_inicio, 'DD/MM/YYYY') AS fecha_inicio,
                to_char(s.fecha_fin, 'DD/MM/YYYY') AS fecha_fin,
                ((s.fecha_fin - s.fecha_inicio) + 1) AS dias_totales,
                s.tipo,
                COALESCE(p.comentario, i.comentario, '---') AS descripcion
            FROM solicitudes s
            LEFT JOIN permisos p ON s.id = p.solicitud_id
            LEFT JOIN incapacidades i ON s.id = i.solicitud_id
            WHERE s.id_uem = %s
            ORDER BY s.fecha_inicio DESC
        """, (session['id_uem'],))
        
        # DataFrames
        df_info = pd.DataFrame({
            '': ['NOMBRE', 'DEPARTAMENTO', 'FECHA DE DESCARGA'],
            'Datos': [usuario[0], usuario[1], datetime.now().strftime("%d/%m/%Y")]
        })

        df_historial = pd.DataFrame(cur.fetchall(), 
            columns=['FECHA INICIO', 'FECHA FIN', 'DÍAS', 'TIPO', 'DESCRIPCIÓN'])  # ✅ Sin "Estado"

        # Generar Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Información
            df_info.to_excel(writer, index=False, startrow=2, header=False)
            
            # Historial
            df_historial.to_excel(writer, index=False, startrow=7)
            
            # Formato
            workbook = writer.book
            worksheet = writer.sheets['Sheet1']
            
            # Títulos
            title_format = workbook.add_format({
                'bold': True,
                'font_size': 14,
                'bg_color': '#2F75B5',
                'font_color': 'white',
                'align': 'center',
                'border': 1
            })
            
            # Encabezados
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#D9E1F2',
                'border': 1,
                'align': 'center'
            })
            
            # Aplicar formatos
            worksheet.merge_range('A2:B2', 'INFORMACIÓN DEL USUARIO', title_format)
            worksheet.merge_range('A7:E7', 'HISTORIAL DE SOLICITUDES', title_format)
            
            for col_num, value in enumerate(df_historial.columns.values):
                worksheet.write(7, col_num, value, header_format)
            
            # Ajustar columnas
            column_widths = {
                'A': 18,  # Campo
                'B': 30,  # Valor
                'C': 12,  # Fecha inicio
                'D': 12,  # Fecha fin
                'E': 8,   # Días
                'F': 15   # Descripción
            }
            
            for col, width in column_widths.items():
                worksheet.set_column(f'{col}:{col}', width)

        output.seek(0)
        filename = f"Tu_Historial_Padi_{datetime.now().strftime('%d_%m_%Y')}.xlsx"
        return send_file(output, 
                        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        download_name=filename,
                        as_attachment=True)

    except Exception as e:
        print(f"Error al generar Excel: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

@app.route('/descargar_historial_admin')
def descargar_historial_admin():
    if 'usuario' not in session or not session.get('es_admin'):
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # main.py (Ruta /descargar_historial_admin)
# main.py (Ruta /descargar_historial_admin)
# main.py (Ruta /descargar_historial_admin)
        cur.execute("""
            SELECT 
                c.nombre_completo,
                c.departamento,
                TO_CHAR(s.fecha_inicio, 'DD/MM/YYYY') AS inicio,
                TO_CHAR(s.fecha_fin, 'DD/MM/YYYY') AS fin,
                (s.fecha_fin - s.fecha_inicio + 1) AS dias,
                s.tipo,
                s.estado,
                COALESCE(p.comentario, i.comentario, '---') AS detalle,
                TO_CHAR(s.creado_en, 'DD/MM/YYYY') AS fecha_peticion  -- ✅ Fecha completa
            FROM solicitudes s
            JOIN colaboradores c ON s.id_uem = c.id_uem
            LEFT JOIN permisos p ON s.id = p.solicitud_id
            LEFT JOIN incapacidades i ON s.id = i.solicitud_id
            ORDER BY s.creado_en DESC  -- Ordenar por fecha de creación
        """)
        
        # 2. Crear DataFrame estructurado
        df = pd.DataFrame(cur.fetchall(), 
        columns=['COLABORADOR', 'DEPARTAMENTO', 'INICIO', 'FIN', 
             'DÍAS', 'TIPO', 'ESTADO', 'DETALLE', 'FECHA DE PETICIÓN'])  # ✅ Nuevo nombre

        # 3. Generar Excel profesional
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Historial General', index=False)
            
            workbook = writer.book
            worksheet = writer.sheets['Historial General']
            
            # Formato profesional
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#2F75B5',  # Azul corporativo
                'font_color': 'white',
                'border': 1,
                'align': 'center'
            })
            
            date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
            
            # Aplicar formatos
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                
            # Ajustar anchos
            column_widths = {
                'A': 25,  # Colaborador
                'B': 20,  # Departamento
                'C': 12,  # Inicio
                'D': 12,  # Fin
                'E': 8,   # Días
                'F': 15,  # Tipo
                'G': 15,  # Estado
                'H': 40,  # Detalle
                'I': 15   # FECHA DE PETICIÓN (nuevo ancho)
            }
            for col, width in column_widths.items():
                worksheet.set_column(f'{col}:{col}', width)

        output.seek(0)
        filename = f"Historial_General_{datetime.now().strftime('%d-%m-%Y')}.xlsx"
        return send_file(output, 
                        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        download_name=filename,
                        as_attachment=True)

    except Exception as e:
        print(f"Error al generar Excel: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

# Modificar ruta de cambio de contraseña
@app.route('/cambiarContraseña', methods=['GET', 'POST'])
def cambiar_contraseña():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    try:
        conn = psycopg2.connect(host=host, database=database, user=user, password=password)
        cur = conn.cursor()
        
        if request.method == 'POST':
            nueva = request.form['contrasena']
            confirmacion = request.form['confirmar_contrasena']
            
            # Validación de coincidencia y formato
            if nueva != confirmacion:
                flash('Las contraseñas no coinciden')
                return redirect(url_for('cambiar_contraseña'))
            if nueva.startswith('TEMP_'):
                flash('No puedes usar formato temporal')
                return redirect(url_for('cambiar_contraseña'))
            
            # Actualizar en BD según si es admin o colaborador
            tabla = 'USUARIO' if session.get('es_admin') else 'colaboradores'
            columna_id = 'id_usuario' if session.get('es_admin') else 'id_uem'
            
            cur.execute(
                f"UPDATE {tabla} SET contrasena = %s WHERE {columna_id} = %s",
                (nueva, session['id_uem'])
            )
            conn.commit()
            
            # Se limpia la sesión para que el usuario vuelva a loguearse con la nueva contraseña
            session.clear()  # Elimina toda la sesión
            flash('Contraseña actualizada. Inicia sesión de nuevo')
            return redirect(url_for('login'))
                    
        return render_template('cambiarContraseña.html')
        
    except Exception as e:
        print(f"Error en cambiar_contraseña: {str(e)}")
        flash('Error al actualizar')
        return redirect(url_for('cambiar_contraseña'))
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/descargar_usuarios')
def descargar_usuarios():
    # Verifica si el usuario está autenticado y es admin
    if 'usuario' not in session or not session.get('es_admin'):
        return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Consulta SQL que une los horarios (hora entrada, hora salida y días de trabajo) 
        # y los consolida con salto de línea para cada usuario
        cur.execute("""
            SELECT 
                c.id_uem,
                c.nombre_completo,
                TO_CHAR(c.fecha_nacimiento, 'DD/MM/YYYY') AS fecha_nacimiento,
                c.direccion,
                c.telefono,
                c.email,
                c.departamento,
                TO_CHAR(c.fecha_contratacion, 'DD/MM/YYYY') AS fecha_contratacion,
                c.usuario,
                STRING_AGG(TO_CHAR(h.horario_entrada, 'HH24:MI'), '\n') AS horario_entrada,
                STRING_AGG(TO_CHAR(h.horario_salida, 'HH24:MI'), '\n') AS horario_salida,
                STRING_AGG(
                    (SELECT STRING_AGG(value::TEXT, ', ') 
                     FROM jsonb_array_elements_text(h.dias_trabajo)), 
                    '\n'
                ) AS dias_trabajo
            FROM colaboradores c
            LEFT JOIN horarios h ON c.id_uem = h.id_uem_fk
            GROUP BY c.id_uem
            ORDER BY c.nombre_completo
        """)
        
        # Definición de las columnas para el DataFrame
        columns = [
            'ID', 'Nombre', 'Fecha Nacimiento', 'Dirección', 'Teléfono', 
            'Email', 'Departamento', 'Fecha Contratación', 'Usuario', 
            'Hora Entrada', 'Hora Salida', 'Días Trabajo'
        ]
        df = pd.DataFrame(cur.fetchall(), columns=columns)
        
        # Generar Excel con formato usando xlsxwriter
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Usuarios')
            
            workbook = writer.book
            worksheet = writer.sheets['Usuarios']
            
            # Formato para celdas que necesiten ajuste de texto
            wrap_format = workbook.add_format({'text_wrap': True})
            
            # Formato para encabezados
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#2F75B5',
                'font_color': 'white',
                'border': 1,
                'align': 'center'
            })
            
            # Escribir encabezados con el formato definido
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Definir el ancho de cada columna (usando letras de Excel)
            column_widths = {
                'A': 8,    # ID
                'B': 30,   # Nombre
                'C': 15,   # Fecha Nacimiento
                'D': 30,   # Dirección
                'E': 12,   # Teléfono
                'F': 25,   # Email
                'G': 20,   # Departamento
                'H': 18,   # Fecha Contratación
                'I': 15,   # Usuario
                'J': 12,   # Hora Entrada
                'K': 12,   # Hora Salida
                'L': 25    # Días Trabajo
            }
            
            for col, width in column_widths.items():
                worksheet.set_column(f'{col}:{col}', width, wrap_format)
        
        output.seek(0)
        filename = f"Lista_Usuarios_{datetime.now().strftime('%d-%m-%Y')}.xlsx"
        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            download_name=filename,
            as_attachment=True
        )
    
    except Exception as e:
        print(f"Error al generar Excel: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()      

# main.py - Asegurar consulta correcta del justificante
@app.route('/obtener_justificante/<int:solicitud_id>')
def obtener_justificante(solicitud_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT justificante, mime_type 
            FROM (
                SELECT justificante, 'application/pdf' as mime_type FROM permisos WHERE solicitud_id = %s
                UNION ALL
                SELECT justificante, 'image/png' as mime_type FROM incapacidades WHERE solicitud_id = %s
                UNION ALL
                SELECT justificante, 'image/jpeg' as mime_type FROM incapacidades WHERE solicitud_id = %s
            ) AS subquery
            LIMIT 1
        """, (solicitud_id, solicitud_id, solicitud_id))
        
        resultado = cur.fetchone()
        
        if resultado:
            # Asegúrate de que el justificante sea un objeto binario y lo codifiques correctamente
            justificante_codificado = base64.b64encode(resultado[0]).decode('utf-8')
            print(f"Justificante codificado: {justificante_codificado[:100]}...")  # Log para depuración
            return jsonify({
                'justificante': justificante_codificado,
                'mime_type': resultado[1]
            })
        
        return jsonify({'error': 'No encontrado'}), 404
    except Exception as e:
        print(f"Error en obtener_justificante: {str(e)}")  # Log para depuración
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()


estados_permitidos = ['PENDIENTE', 'APROBADO', 'RECHAZADO']

@app.route('/actualizar_solicitud/<int:solicitud_id>', methods=['PUT'])
def actualizar_solicitud(solicitud_id):
    conn = None
    cursor = None
    try:
        data = request.get_json()
        # Se requieren 'estado' y 'comentario'. 'motivo_cambio' es opcional.
        if 'estado' not in data or 'comentario' not in data:
            return jsonify({"error": "Faltan datos necesarios: 'estado' y/o 'comentario'"}), 400

        estado_nuevo = data['estado']
        admin_comentario = data['comentario'].strip()
        motivo_cambio = data.get('motivo_cambio', '').strip()

        # Verificamos que el nuevo estado esté dentro de los permitidos
        if estado_nuevo not in ['PENDIENTE', 'APROBADO', 'RECHAZADO']:
            return jsonify({"error": "El estado no es válido para esta solicitud."}), 400

        if 'id_uem' not in session:
            return jsonify({"error": "No estás autenticado."}), 401

        id_usuario = session['id_uem']

        conn = psycopg2.connect(host=host, database=database, user=user, password=password)
        cursor = conn.cursor()

        # Obtener el estado actual de la solicitud
        cursor.execute("SELECT estado FROM solicitudes WHERE id = %s", (solicitud_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Solicitud no encontrada."}), 404
        estado_actual = row[0]

        # Si el estado ya es APROBADO o RECHAZADO y se intenta actualizar con el mismo, no permitir
        if estado_actual in ['APROBADO', 'RECHAZADO'] and estado_actual == estado_nuevo:
            mensaje = "Esto ya está validado." if estado_actual == "APROBADO" else "Esto ya está rechazado."
            return jsonify({"error": mensaje}), 400

        # Verificar si ya existe una validación para esta solicitud por este admin
        cursor.execute("""
            SELECT id FROM validaciones
            WHERE solicitud_id = %s AND id_usuario = %s
            ORDER BY id ASC LIMIT 1
        """, (solicitud_id, id_usuario))
        existing = cursor.fetchone()
        if existing:
            # Actualizar la validación existente
            validation_id = existing[0]
            cursor.execute("""
                UPDATE validaciones
                SET estado_anterior = %s,
                    estado_nuevo = %s,
                    comentario = %s,
                    motivo_cambio = %s,
                    fecha_validacion = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (estado_actual, estado_nuevo, admin_comentario, motivo_cambio, validation_id))
        else:
            # Insertar nueva validación
            cursor.execute("""
                INSERT INTO validaciones (solicitud_id, id_usuario, estado_anterior, estado_nuevo, comentario, motivo_cambio)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (solicitud_id, id_usuario, estado_actual, estado_nuevo, admin_comentario, motivo_cambio))

        # Actualizar el estado de la solicitud
        cursor.execute("""
            UPDATE solicitudes
            SET estado = %s
            WHERE id = %s
        """, (estado_nuevo, solicitud_id))

        conn.commit()
        return jsonify({"message": "Solicitud actualizada correctamente."}), 200

    except Exception as e:
        print(f"Error inesperado: {str(e)}")
        return jsonify({"error": f"Error al actualizar la solicitud: {str(e)}"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/obtener_validacion/<int:solicitud_id>')
def obtener_validacion(solicitud_id):
    if 'id_uem' not in session:
        return jsonify({"error": "No estás autenticado."}), 401
    try:
        conn = psycopg2.connect(host=host, database=database, user=user, password=password)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, comentario, motivo_cambio 
            FROM validaciones 
            WHERE solicitud_id = %s AND id_usuario = %s
            ORDER BY id ASC LIMIT 1
        """, (solicitud_id, session['id_uem']))
        record = cursor.fetchone()
        if record:
            validation_id, comentario, motivo_cambio = record
            return jsonify({
                "validation_id": validation_id,
                "comentario": comentario,
                "motivo_cambio": motivo_cambio
            })
        else:
            return jsonify({"validation_id": None, "comentario": "", "motivo_cambio": ""})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()





# main.py - Nuevo endpoint para contador
@app.route('/contador_cambios/<int:solicitud_id>')
def contador_cambios(solicitud_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM validaciones WHERE solicitud_id = %s
        """, (solicitud_id,))
        contador = cur.fetchone()[0]
        return jsonify({'contador': contador})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# main.py - Modificar el filtro del template
@app.template_filter('mes_anio')
def mes_anio_filter(fecha):
    try:
        if isinstance(fecha, str):  # Si es string, convertir a datetime
            fecha = datetime.strptime(fecha, "%d/%m/%Y")
        return fecha.strftime("%B %Y").capitalize()  # Ej: "Enero 2024"
    except:
        return "Fecha inválida"

if __name__ == '__main__':
    app.run(debug=True)
