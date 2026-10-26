from app import auth_bp
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/auth/register", methods=["POST"])
def registrar_usuario():
    return {}


@auth_bp.route("/auth/login", methods=["POST"])
def iniciar_sesion():
    return {}


@auth_bp.route("/usuarios/me", methods=["GET"])
def obtener_usuario_actual():
    return {}


@auth_bp.route("/usuarios/me/historial", methods=["GET"])
def obtener_historial_usuario():
    return {}