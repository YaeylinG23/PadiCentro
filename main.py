#Librerias y framework
from flask import Flask, request, render_template, redirect, url_for, session 
# Flask: Framework para crear la aplicación web.
# request: Maneja solicitudes HTTP (obtener datos de formularios, parámetros, etc.).
# render_template: Renderiza plantillas HTML dinámicas con contenido.
# redirect: Redirige al usuario a otra URL.
# url_for: Genera dinámicamente las URLs según las rutas definidas.
# session: Gestiona datos de sesión del usuario (cookies cifradas).
import pandas as pd  
# Librería para manipular y analizar datos (no se usa en este código, pero se puede utilizar en el futuro).
import psycopg2  
# Conecta e interactúa con bases de datos PostgreSQL.


app = Flask(__name__)  
# Crea una instancia de la aplicación Flask.
app.secret_key = 'Contreseña'  
# Clave secreta necesaria para manejar las sesiones de forma segura. Se recomienda cambiarla en producción y no exponerla.


#Conexión a la base de datos
host='localhost'  # Cambia si estás usando un servidor remoto
database='postgres'  # Nombre de tu base de datos
user='postgres'    # Usuario de PostgreSQL
password='Padi02'  # Contraseña del usuario


#Conexión con el login
@app.route('/', methods=['GET', 'POST'])  
# Define la ruta principal ('/') y permite manejar solicitudes GET (mostrar el formulario) y POST (procesar el formulario).
def login():  
    if request.method == 'POST':  
        # Si el método es POST, significa que el usuario envió el formulario.
        nombre = request.form['nombre']  
        # Obtiene el valor del campo 'nombre' del formulario enviado.
        contrasena = request.form['contrasena']  
        # Obtiene el valor del campo 'contrasena' del formulario.
        try:  
            # Intenta conectarse a la base de datos.
            conexion = psycopg2.connect(  
                host=host,
                database=database,
                user=user,
                password=password
            )  
            # Establece una conexión con la base de datos.
            cursor = conexion.cursor()  
            # Crea un cursor para ejecutar consultas SQL.
            query = "SELECT * FROM USUARIO WHERE nombre = %s AND contrasena = %s"  
            # Consulta SQL para buscar al usuario con el nombre y contraseña proporcionados.
            cursor.execute(query, (nombre, contrasena))  
            # Ejecuta la consulta, previniendo inyecciones SQL con parámetros.
            usuario = cursor.fetchone()  
            # Obtiene el primer resultado (si existe).
            if usuario:  
                # Si el usuario existe en la base de datos:
                session['usuario'] = nombre  
                # Guarda el nombre del usuario en la sesión para identificarlo.
                return redirect(url_for('dashboard'))  
                # Redirige al usuario a la página principal (dashboard).
            else:  
                # Si no se encuentra el usuario:
                error = "Nombre de usuario o contraseña incorrectos"  
                # Mensaje de error.
                return render_template('login.html', error=error)  
                # Renderiza nuevamente la página de login con el mensaje de error.
        except Exception as error:  
            # Si ocurre un error durante la conexión o consulta:
            return f"Error al conectar a la base de datos: {error}"  
            # Devuelve un mensaje con el error.
        finally:  
            # Bloque que se ejecuta siempre (haya error o no).
            if 'cursor' in locals():  
                cursor.close()  
                # Cierra el cursor si se creó.
            if 'conexion' in locals():  
                conexion.close()  
                # Cierra la conexión a la base de datos si se creó.
    return render_template('login.html')  
    # Si el método es GET (el usuario abre la página por primera vez), renderiza el formulario de login.


#Página principal
@app.route('/dashboard')  
# Define la ruta '/dashboard'.
def dashboard():  
    if 'usuario' in session:  
        # Comprueba si hay un usuario logueado en la sesión.
        return render_template('dashboard.html', nombre=session['usuario'])  
        # Renderiza la página principal con el nombre del usuario.
    else:  
        # Si no hay sesión activa:
        return redirect(url_for('login'))  
        # Redirige al login.


#Cerrar sesión
@app.route('/logout')  
# Define la ruta '/logout'.
def logout():  
    session.pop('usuario', None)  
    # Elimina la sesión del usuario (si existe).
    return redirect(url_for('login'))  
    # Redirige al login después de cerrar la sesión.


# Ejecutar la aplicación
if __name__ == '__main__':  
    # Si este archivo se ejecuta directamente (no importado como módulo):
    app.run(debug=True)  
    # Ejecuta la aplicación Flask en modo de depuración (para detectar errores y hacer pruebas).
