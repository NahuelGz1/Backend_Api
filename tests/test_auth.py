import os
import smtplib
import unittest
import uuid
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import pymysql

from app import create_app
from app.repositories.auth_repository import buscar_por_email, restablecer_password
from app.utils.security import hashear_contraseña, verificar_contraseña


@unittest.skipUnless(os.getenv("TEST_DB_PORT"), "Requiere MySQL aislado en TEST_DB_PORT")
class AuthMySQLTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database = "test_auth_" + uuid.uuid4().hex
        cls.env = patch.dict(os.environ, {
            "DB_HOST": "127.0.0.1", "DB_PORT": os.environ["TEST_DB_PORT"],
            "DB_USER": "root", "DB_PASSWORD": "", "DB_NAME": cls.database,
        })
        cls.env.start()
        cls.root = pymysql.connect(
            host="127.0.0.1", port=int(os.environ["TEST_DB_PORT"]),
            user="root", password="", autocommit=True,
        )
        with cls.root.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE `{cls.database}`")
            cursor.execute(f"USE `{cls.database}`")
            cursor.execute("""CREATE TABLE usuarios (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                rol VARCHAR(20) NOT NULL
            )""")
        cls.app = create_app({
            "TESTING": True, "JWT_SECRET_KEY": "test-key-not-for-production-123456789",
            "SMTP_STARTTLS": False,
        })

    @classmethod
    def tearDownClass(cls):
        with cls.root.cursor() as cursor:
            cursor.execute(f"DROP DATABASE `{cls.database}`")
        cls.root.close()
        cls.env.stop()

    def setUp(self):
        with self.root.cursor() as cursor:
            cursor.execute("DELETE FROM usuarios")
        self.client = self.app.test_client()

    def register(self, **extra):
        return self.client.post("/api/auth/register", json={
            "nombre": "Persona Prueba", "email": "persona@example.test",
            "password": "Password-inicial-67", **extra,
        })

    def login(self, password="Password-inicial-67"):
        return self.client.post("/api/auth/login", json={
            "email": "persona@example.test", "password": password,
        })

    def test_registro_hash_rol_duplicado_y_login(self):
        response = self.register(rol="administrador")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["data"]["rol"], "cliente")
        usuario = buscar_por_email("persona@example.test")
        self.assertNotEqual(usuario["password_hash"], "Password-inicial-67")
        self.assertTrue(verificar_contraseña("Password-inicial-67", usuario["password_hash"]))
        self.assertEqual(self.register().status_code, 409)
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("password_hash", response.get_data(as_text=True))
        token = response.json["data"]["token"]
        perfil = self.client.get("/api/auth/usuarios/me", headers={"Authorization": "Bearer " + token})
        self.assertEqual(perfil.status_code, 200)
        self.assertEqual(perfil.json["data"]["rol"], "cliente")
        self.assertEqual(self.login("incorrecta").status_code, 401)

    def test_rol_admin_y_autorizacion_actualizada_desde_sql(self):
        self.register()
        with self.root.cursor() as cursor:
            cursor.execute("UPDATE usuarios SET rol = %s", ("administrador",))
        login = self.login()
        self.assertEqual(login.json["data"]["usuario"]["rol"], "administrador")
        token = login.json["data"]["token"]
        with self.root.cursor() as cursor:
            cursor.execute("UPDATE usuarios SET rol = %s", ("cliente",))
        response = self.client.post("/api/peliculas", json={}, headers={"Authorization": "Bearer " + token})
        self.assertEqual(response.status_code, 403)

    def test_entrada_json_invalida_y_campos(self):
        for ruta in ("register", "login", "forgot-password", "reset-password"):
            for datos in ([], None, "texto", 12):
                with self.subTest(ruta=ruta, datos=datos):
                    respuesta = self.client.post(f"/api/auth/{ruta}", json=datos)
                    self.assertEqual(respuesta.status_code, 400)
                    self.assertFalse(respuesta.json["ok"])
        for campos in ({"nombre": ""}, {"email": "invalido"}, {"password": 17}, {"password": "corta"}):
            self.assertEqual(self.register(**campos).status_code, 400)
        self.assertEqual(self.client.get("/api/auth/login").status_code, 405)
        self.assertEqual(self.client.get("/api/auth/usuarios/me").status_code, 401)

    def test_sql_parametrizado_no_ejecuta_inyeccion(self):
        self.register(nombre="Robert'); DROP TABLE usuarios;--")
        self.assertEqual(self.login().status_code, 200)
        response = self.client.post("/api/auth/login", json={
            "email": "x'OR'1'='1@example.test", "password": "Password-inicial-67",
        })
        self.assertEqual(response.status_code, 401)

    def test_recuperacion_actualiza_hash_invalida_token_y_sesiones(self):
        self.register()
        acceso = self.login().json["data"]["token"]
        with patch("app.services.email_service.smtplib.SMTP") as smtp:
            smtp.return_value.__enter__.return_value.send_message.return_value = {}
            token = self.token_recuperacion_smtp(smtp)
        response = self.client.post("/api/auth/reset-password", json={
            "token": token, "password": "Password-nueva-67",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.login().status_code, 401)
        self.assertEqual(self.login("Password-nueva-67").status_code, 200)
        self.assertEqual(self.client.post("/api/auth/reset-password", json={
            "token": token, "password": "Otra-password-67",
        }).status_code, 400)
        self.assertEqual(self.client.get("/api/auth/usuarios/me", headers={
            "Authorization": "Bearer " + acceso,
        }).status_code, 401)

    def token_recuperacion_smtp(self, smtp):
        response = self.client.post("/api/auth/forgot-password", json={"email": "persona@example.test"})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json["data"])
        mensaje = smtp.return_value.__enter__.return_value.send_message.call_args.args[0]
        enlace = next(line for line in mensaje.get_content().splitlines() if line.startswith("http"))
        token = parse_qs(urlsplit(enlace).query)["token"][0]
        self.assertNotIn(token, response.get_data(as_text=True))
        return token

    def test_recuperacion_privacidad_vencimiento_firma_y_error_smtp(self):
        self.register()
        with patch("app.services.email_service.smtplib.SMTP") as smtp:
            smtp.return_value.__enter__.return_value.send_message.return_value = {}
            token = self.token_recuperacion_smtp(smtp)
            conocido = self.client.post("/api/auth/forgot-password", json={"email": "persona@example.test"})
            smtp.reset_mock()
            desconocido = self.client.post("/api/auth/forgot-password", json={"email": "ausente@example.test"})
            self.assertEqual(conocido.json, desconocido.json)
            smtp.assert_not_called()
        for invalido in (token + "x", "invalido"):
            self.assertEqual(self.client.post("/api/auth/reset-password", json={
                "token": invalido, "password": "Password-nueva-67",
            }).status_code, 400)
        with patch.dict(self.app.config, {"PASSWORD_RESET_MAX_AGE": -1}):
            self.assertEqual(self.client.post("/api/auth/reset-password", json={
                "token": token, "password": "Password-nueva-67",
            }).status_code, 400)
        with patch("app.services.email_service.smtplib.SMTP", side_effect=smtplib.SMTPException):
            self.assertEqual(self.client.post("/api/auth/forgot-password", json={
                "email": "persona@example.test",
            }).status_code, 503)

    def test_update_condicional_no_reutiliza_hash_anterior(self):
        self.register()
        usuario = buscar_por_email("persona@example.test")
        nuevo = hashear_contraseña("Password-nueva-67")
        self.assertEqual(restablecer_password(usuario["id"], usuario["password_hash"], nuevo), 1)
        self.assertEqual(restablecer_password(usuario["id"], usuario["password_hash"], nuevo), 0)


if __name__ == "__main__":
    unittest.main()
