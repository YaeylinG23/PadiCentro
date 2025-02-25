#Librerias y framework
from flask import Flask, request, render_template, redirect, url_for, session, make_response, jsonify, send_file
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


app = Flask(__name__)
app.secret_key = 'Contreseña'

class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        if isinstance(obj, datetime.time):
            return obj.strftime('%H:%M:%S')
        return super().default(obj)


app.json_provider_class = CustomJSONProvider
app.json = app.json_provider_class(app)

#Conexión a la base de datos
host='localhost'
database='postgres2'
user='postgres'
password='024689'


#Conexión con el login
@app.route('/', methods=['GET', 'POST'])
def login():
    if 'usuario' in session:  
        return redirect(url_for('dashboard_admin' if session.get('es_admin') else 'dashboard_empleados'))
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        contrasena = request.form['contrasena']
        
        try:
            conexion = psycopg2.connect(host=host, database=database, user=user, password=password)
            cursor = conexion.cursor()

            # Primero verificar si es admin
            cursor.execute("SELECT * FROM USUARIO WHERE nombre = %s AND contrasena = %s", (nombre, contrasena))
            usuario = cursor.fetchone()
            
            if usuario:
                session['usuario'] = nombre
                session['es_admin'] = True
                return redirect(url_for('dashboard_admin'))
            else:
                # Si no es admin, verificar colaboradores
                cursor.execute("SELECT * FROM colaboradores WHERE usuario = %s AND contrasena = %s", (nombre, contrasena))
                empleado = cursor.fetchone()
                
                if empleado:
                    session['usuario'] = nombre
                    session['es_admin'] = False
                    return redirect(url_for('dashboard_empleados'))
                else:
                    error = "Credenciales incorrectas"
                    return render_template('login.html', error=error)

        except Exception as error:
            return f"Error: {error}"
        finally:
            if 'cursor' in locals(): cursor.close()
            if 'conexion' in locals(): conexion.close()
    response = make_response(render_template('login.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

#Página principal del administrador
@app.route('/dashboard_admin')
def dashboard_admin():
    if 'usuario' in session:
        response = make_response(render_template('Admin/dashboard_admin.html', nombre=session['usuario']))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    else:
        return redirect(url_for('login'))

# Función para enviar el correo
EMAIL_EMISOR = 'garciayaytube@gmail.com'
EMAIL_CONTRA  = 'tczj qcuu npyd ijwe'

def send_email(user, password, receptor):
    asunto = "Tus credenciales de acceso"
    cuerpo = f"""
    Tu usuario es: {user}
    Tu contraseña es: {password}

    Saludos,
    Equipo de Recursos Humanos.
    """

    em = EmailMessage()
    em["From"] = EMAIL_EMISOR
    em["To"] = receptor
    em["Subject"] = asunto
    em.set_content(cuerpo)

    contexto = ssl.create_default_context()

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=contexto) as smtp:
            smtp.login(EMAIL_EMISOR, EMAIL_CONTRA)
            smtp.sendmail(EMAIL_EMISOR, receptor, em.as_string())
        return True
    except Exception as e:
        print(f"Error al enviar el correo: {e}")
        return False

# Añadir empleados
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
                        data['contrasena']
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
                            Json(horario['dias'])
                        ))
                    
                    conn.commit()

            # Enviar correo con las credenciales
            if send_email(data['usuario'], data['contrasena'], data['email']):
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

#Sistema de asistencias para Admin
@app.route('/asistencias')
def asistencias():
    return render_template('Admin/asistencias.html')

# Ruta para historial de empleados (Admin)
@app.route('/historial_empleados')
def historial_empleados():
    return render_template('Admin/historial_empleados.html')

#Botón para generar credenciales
def generar_contrasena(longitud=12):
    caracteres = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(caracteres) for _ in range(longitud))

@app.route('/generar_contrasena')
def generar():
    contrasena = generar_contrasena()
    return jsonify({'contrasena': contrasena})

#Cerrar sesión
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    session.pop('es_admin', None)
    return redirect(url_for('login'))

# Gestión de empleados
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

# Ruta para eliminar colaborador
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

# Ruta para obtener datos de un colaborador (ahora con fechas formateadas)
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
                    'fecha_nacimiento': colaborador[2],
                    'direccion': colaborador[3],
                    'telefono': colaborador[4],
                    'email': colaborador[5],
                    'departamento': colaborador[6],
                    'fecha_contratacion': colaborador[7],
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





# Ruta para actualizar colaborador
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


#Página principal del usuario
@app.route('/dashboard_empleados')
def dashboard_empleados():
    if 'usuario' in session and not session.get('es_admin'):
        return render_template('Empleados/dashboard_empleados.html', nombre=session['usuario'])
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
