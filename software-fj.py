"""
Sistema Integral de Gestión de Clientes, Servicios y Reservas - Software FJ
Curso: Programación (213023) - UNAD
Arquitectura Orientada a Objetos en memoria (sin base de datos) con manejo
avanzado de excepciones, sobrecarga por parámetros opcionales y archivo de logs.
"""

from abc import ABC, abstractmethod
from datetime import datetime
import logging
import re

# ==============================================================================
# 1. CONFIGURACIÓN DEL ARCHIVO DE LOGS (EVENTOS Y ERRORES)
# ==============================================================================
logger = logging.getLogger("SoftwareFJ")
logger.setLevel(logging.INFO)
logger.handlers.clear()

# Se crea y sobrescribe 'software_fj.log' en cada ejecución para registrar eventos y errores
_file_handler = logging.FileHandler("software_fj.log", mode="w", encoding="utf-8")
_formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
_file_handler.setFormatter(_formatter)
logger.addHandler(_file_handler)


# ==============================================================================
# 2. EXCEPCIONES PERSONALIZADAS
# ==============================================================================
class ErrorSistemaFJ(Exception):
    """Excepción base para todos los errores controlados del sistema."""


class DatoInvalidoError(ErrorSistemaFJ):
    """Se lanza cuando un dato tiene formato incorrecto o valor fuera de regla."""


class ParametroFaltanteError(ErrorSistemaFJ):
    """Se lanza cuando falta un parámetro obligatorio o llega vacío."""


class ServicioNoDisponibleError(ErrorSistemaFJ):
    """Se lanza cuando no hay disponibilidad, stock o el servicio está inactivo."""


class OperacionReservaError(ErrorSistemaFJ):
    """Se lanza cuando falla la creación, confirmación o cancelación de una reserva."""


class CalculoInconsistenteError(ErrorSistemaFJ):
    """Se lanza cuando hay tarifas, descuentos, impuestos o totales inválidos."""


# ==============================================================================
# 3. CLASE ABSTRACTA GENERAL DEL SISTEMA
# ==============================================================================
class EntidadSistema(ABC):
    """Clase abstracta base para entidades gestionadas en Software FJ."""

    def __init__(self, id_entidad: str):
        # Valida que exista un identificador no vacío
        if id_entidad is None or not str(id_entidad).strip():
            raise ParametroFaltanteError("El ID de la entidad es obligatorio.")
        self._id_entidad = str(id_entidad).strip()
        self._fecha_creacion = datetime.now()

    @property
    def id_entidad(self) -> str:
        """Retorna el identificador único de la entidad."""
        return self._id_entidad

    @property
    def fecha_creacion(self) -> datetime:
        """Retorna la fecha y hora de creación en memoria."""
        return self._fecha_creacion

    @abstractmethod
    def resumen(self) -> str:
        """Método abstracto que cada subclase debe implementar."""


# ==============================================================================
# 4. CLASE CLIENTE (ENCAPSULACIÓN Y VALIDACIONES ESTRICTAS)
# ==============================================================================
class Cliente(EntidadSistema):
    """Representa un cliente con datos encapsulados y validados."""

    def __init__(self, id_cliente: str, nombre: str, correo: str, activo: bool = True):
        super().__init__(id_cliente)
        # Usa los setters para aplicar validaciones desde la creación
        self.nombre = nombre
        self.correo = correo
        self._activo = bool(activo)
        logger.info(f"Cliente registrado: {self._id_entidad} - {self._nombre}")

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        if valor is None or not str(valor).strip():
            raise ParametroFaltanteError("El nombre del cliente no puede estar vacío.")
        limpio = str(valor).strip()
        if len(limpio) < 3:
            raise DatoInvalidoError(f"Nombre demasiado corto: '{limpio}'.")
        self._nombre = limpio

    @property
    def correo(self) -> str:
        return self._correo

    @correo.setter
    def correo(self, valor: str) -> None:
        if valor is None or not str(valor).strip():
            raise ParametroFaltanteError("El correo electrónico es obligatorio.")
        limpio = str(valor).strip()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", limpio):
            raise DatoInvalidoError(f"Correo electrónico inválido: '{limpio}'.")
        self._correo = limpio

    @property
    def activo(self) -> bool:
        return self._activo

    def desactivar(self) -> None:
        """Desactiva el cliente para impedir nuevas reservas."""
        self._activo = False
        logger.info(f"Cliente desactivado: {self._id_entidad}")

    def resumen(self) -> str:
        estado = "Activo" if self._activo else "Inactivo"
        return f"Cliente[{self._id_entidad}] {self._nombre} ({self._correo}) - {estado}"


# ==============================================================================
# 5. CLASE ABSTRACTA SERVICIO Y 3 SERVICIOS ESPECIALIZADOS
# ==============================================================================
class Servicio(EntidadSistema, ABC):
    """Clase abstracta para los servicios ofrecidos por Software FJ."""

    def __init__(self, id_servicio: str, nombre: str, tarifa_base: float, disponible: bool = True):
        super().__init__(id_servicio)
        if nombre is None or not str(nombre).strip():
            raise ParametroFaltanteError("El nombre del servicio es obligatorio.")
        try:
            tarifa = float(tarifa_base)
        except (TypeError, ValueError) as exc:
            raise DatoInvalidoError("La tarifa base debe ser un número válido.") from exc

        if tarifa <= 0:
            raise CalculoInconsistenteError("La tarifa base debe ser mayor que cero.")

        self._nombre = str(nombre).strip()
        self._tarifa_base = tarifa
        self._disponible = bool(disponible)

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def tarifa_base(self) -> float:
        return self._tarifa_base

    @property
    def disponible(self) -> bool:
        return self._disponible

    @disponible.setter
    def disponible(self, estado: bool) -> None:
        self._disponible = bool(estado)

    @abstractmethod
    def validar_parametros(self, duracion_horas: float, **kwargs) -> None:
        """Valida parámetros específicos de cada tipo de servicio."""

    @abstractmethod
    def describir(self) -> str:
        """Describe las características del servicio."""

    @abstractmethod
    def _subtotal_por_duracion(self, duracion_horas: float, **kwargs) -> float:
        """Calcula el subtotal base antes de descuentos e impuestos."""

    def calcular_costo(
        self,
        duracion_horas: float = 1.0,
        descuento_pct: float = 0.0,
        impuesto_pct: float = 0.0,
        **kwargs,
    ) -> float:
        """
        Sobrecarga por parámetros opcionales y palabras clave:
        - calcular_costo(2)
        - calcular_costo(2, descuento_pct=10)
        - calcular_costo(2, descuento_pct=10, impuesto_pct=19, asistentes=5)
        """
        self.validar_parametros(duracion_horas, **kwargs)

        try:
            desc = float(descuento_pct)
            imp = float(impuesto_pct)
        except (TypeError, ValueError) as exc:
            raise DatoInvalidoError("Descuento e impuesto deben ser numéricos.") from exc

        if not (0.0 <= desc < 100.0):
            raise CalculoInconsistenteError(f"Descuento inválido ({desc}%): debe estar entre 0 y <100.")
        if imp < 0.0:
            raise CalculoInconsistenteError(f"Impuesto inválido ({imp}%): no puede ser negativo.")

        subtotal = self._subtotal_por_duracion(duracion_horas, **kwargs)
        con_descuento = subtotal * (1.0 - desc / 100.0)
        total = con_descuento * (1.0 + imp / 100.0)

        if total <= 0:
            raise CalculoInconsistenteError("El costo total calculado no es válido.")

        return round(total, 2)

    def resumen(self) -> str:
        return self.describir()


class ReservaSala(Servicio):
    """Servicio especializado para reserva de salas."""

    def __init__(self, id_servicio: str, nombre: str, tarifa_base: float, capacidad_maxima: int):
        super().__init__(id_servicio, nombre, tarifa_base, disponible=True)
        try:
            cap = int(capacidad_maxima)
        except (TypeError, ValueError) as exc:
            raise DatoInvalidoError("La capacidad máxima debe ser entera.") from exc
        if cap <= 0:
            raise DatoInvalidoError("La capacidad máxima de la sala debe ser mayor que cero.")
        self._capacidad_maxima = cap

    def validar_parametros(self, duracion_horas: float, **kwargs) -> None:
        if duracion_horas is None or float(duracion_horas) <= 0:
            raise DatoInvalidoError("La duración en horas debe ser mayor que cero.")
        if "asistentes" not in kwargs or kwargs["asistentes"] is None:
            raise ParametroFaltanteError("Falta el parámetro 'asistentes' para reservar la sala.")
        asistentes = int(kwargs["asistentes"])
        if asistentes <= 0:
            raise DatoInvalidoError("El número de asistentes debe ser mayor que cero.")
        if asistentes > self._capacidad_maxima:
            raise DatoInvalidoError(
                f"Asistentes ({asistentes}) exceden capacidad ({self._capacidad_maxima})."
            )

    def _subtotal_por_duracion(self, duracion_horas: float, **kwargs) -> float:
        asistentes = int(kwargs["asistentes"])
        # Recargo del 15% si supera la mitad de la capacidad de la sala
        recargo = 1.15 if asistentes > (self._capacidad_maxima // 2) else 1.0
        return float(duracion_horas) * self._tarifa_base * recargo

    def describir(self) -> str:
        estado = "Disponible" if self._disponible else "No disponible"
        return (
            f"Sala [{self._id_entidad}] {self._nombre} | Cap: {self._capacidad_maxima} | "
            f"Tarifa/h: ${self._tarifa_base:.2f} | {estado}"
        )


class AlquilerEquipo(Servicio):
    """Servicio especializado para alquiler de equipos."""

    def __init__(self, id_servicio: str, nombre: str, tarifa_base: float, unidades_disponibles: int):
        try:
            unidades = int(unidades_disponibles)
        except (TypeError, ValueError) as exc:
            raise DatoInvalidoError("Las unidades disponibles deben ser un número entero.") from exc
        if unidades < 0:
            raise DatoInvalidoError("Las unidades disponibles no pueden ser negativas.")

        super().__init__(id_servicio, nombre, tarifa_base, disponible=(unidades > 0))
        self._unidades_disponibles = unidades

    def validar_parametros(self, duracion_horas: float, **kwargs) -> None:
        if duracion_horas is None or float(duracion_horas) <= 0:
            raise DatoInvalidoError("La duración del alquiler debe ser mayor que cero.")
        unidades = int(kwargs.get("unidades", 1))
        if unidades <= 0:
            raise DatoInvalidoError("Debe solicitar al menos 1 unidad.")
        if not self._disponible or unidades > self._unidades_disponibles:
            raise ServicioNoDisponibleError(
                f"Unidades insuficientes para '{self._nombre}' (solicitadas: {unidades}, disponibles: {self._unidades_disponibles})."
            )

    def _subtotal_por_duracion(self, duracion_horas: float, **kwargs) -> float:
        unidades = int(kwargs.get("unidades", 1))
        return float(duracion_horas) * self._tarifa_base * unidades

    def describir(self) -> str:
        estado = "Disponible" if self._disponible else "No disponible"
        return (
            f"Equipo [{self._id_entidad}] {self._nombre} | Stock: {self._unidades_disponibles} | "
            f"Tarifa/h: ${self._tarifa_base:.2f} | {estado}"
        )


class AsesoriaEspecializada(Servicio):
    """Servicio especializado para asesorías técnicas o de software."""

    def __init__(self, id_servicio: str, nombre: str, tarifa_base: float, especialidad: str):
        super().__init__(id_servicio, nombre, tarifa_base, disponible=True)
        if especialidad is None or not str(especialidad).strip():
            raise ParametroFaltanteError("La especialidad de la asesoría es obligatoria.")
        self._especialidad = str(especialidad).strip()

    def validar_parametros(self, duracion_horas: float, **kwargs) -> None:
        if duracion_horas is None or float(duracion_horas) < 1:
            raise DatoInvalidoError("La asesoría especializada requiere mínimo 1 hora.")

    def _subtotal_por_duracion(self, duracion_horas: float, **kwargs) -> float:
        # Incluye cargo fijo inicial de apertura ($25) más horas contratadas
        return 25.0 + (float(duracion_horas) * self._tarifa_base)

    def describir(self) -> str:
        estado = "Disponible" if self._disponible else "No disponible"
        return (
            f"Asesoría [{self._id_entidad}] {self._nombre} ({self._especialidad}) | "
            f"Tarifa/h: ${self._tarifa_base:.2f} | {estado}"
        )


# ==============================================================================
# 6. CLASE RESERVA Y GESTOR EN MEMORIA
# ==============================================================================
class Reserva(EntidadSistema):
    """Integra cliente, servicio, duración, costo y estados de la reserva."""

    def __init__(
        self,
        id_reserva: str,
        cliente: Cliente,
        servicio: Servicio,
        duracion_horas: float,
        descuento_pct: float = 0.0,
        impuesto_pct: float = 0.0,
        **detalle_servicio,
    ):
        super().__init__(id_reserva)

        if not isinstance(cliente, Cliente):
            raise DatoInvalidoError("El cliente debe ser una instancia de Cliente.")
        if not isinstance(servicio, Servicio):
            raise DatoInvalidoError("El servicio debe ser una instancia de Servicio.")
        if not cliente.activo:
            raise OperacionReservaError(f"El cliente '{cliente.nombre}' está inactivo.")
        if not servicio.disponible:
            raise ServicioNoDisponibleError(f"El servicio '{servicio.nombre}' no está disponible.")

        self._cliente = cliente
        self._servicio = servicio
        self._duracion_horas = float(duracion_horas)
        self._estado = "PENDIENTE"
        self._costo_total = servicio.calcular_costo(
            duracion_horas=self._duracion_horas,
            descuento_pct=descuento_pct,
            impuesto_pct=impuesto_pct,
            **detalle_servicio,
        )

    @property
    def estado(self) -> str:
        return self._estado

    @property
    def costo_total(self) -> float:
        return self._costo_total

    def confirmar(self) -> None:
        """Confirma la reserva si no está cancelada."""
        if self._estado == "CANCELADA":
            raise OperacionReservaError(
                f"No se puede confirmar la reserva {self._id_entidad}: está cancelada."
            )
        self._estado = "CONFIRMADA"
        logger.info(
            f"Reserva CONFIRMADA {self._id_entidad} | Cliente: {self._cliente.nombre} | "
            f"Servicio: {self._servicio.nombre} | Total: ${self._costo_total:.2f}"
        )

    def cancelar(self, motivo: str = "Cancelada por solicitud del cliente") -> None:
        """Cancela la reserva si aún no fue cancelada previamente."""
        if self._estado == "CANCELADA":
            raise OperacionReservaError(f"La reserva {self._id_entidad} ya está cancelada.")
        self._estado = "CANCELADA"
        logger.info(f"Reserva CANCELADA {self._id_entidad} | Motivo: {motivo}")

    def resumen(self) -> str:
        return (
            f"Reserva[{self._id_entidad}] {self._estado} | Cliente: {self._cliente.nombre} | "
            f"Servicio: {self._servicio.nombre} | Duración: {self._duracion_horas}h | "
            f"Total: ${self._costo_total:.2f}"
        )


class GestorSoftwareFJ:
    """Gestiona colecciones en memoria (listas) sin usar bases de datos."""

    def __init__(self):
        self.clientes: list[Cliente] = []
        self.servicios: list[Servicio] = []
        self.reservas: list[Reserva] = []

    def registrar_cliente(self, cliente: Cliente) -> str:
        if any(c.id_entidad == cliente.id_entidad for c in self.clientes):
            raise DatoInvalidoError(f"Ya existe un cliente con ID '{cliente.id_entidad}'.")
        self.clientes.append(cliente)
        return cliente.resumen()

    def registrar_servicio(self, servicio: Servicio) -> str:
        if any(s.id_entidad == servicio.id_entidad for s in self.servicios):
            raise DatoInvalidoError(f"Ya existe un servicio con ID '{servicio.id_entidad}'.")
        self.servicios.append(servicio)
        return servicio.resumen()

    def crear_y_confirmar_reserva(
        self,
        id_reserva: str,
        id_cliente: str,
        id_servicio: str,
        duracion_horas: float,
        descuento_pct: float = 0.0,
        impuesto_pct: float = 0.0,
        **detalle_servicio,
    ) -> str:
        try:
            cliente = next((c for c in self.clientes if c.id_entidad == id_cliente), None)
            servicio = next((s for s in self.servicios if s.id_entidad == id_servicio), None)

            if cliente is None:
                raise ParametroFaltanteError(f"Cliente '{id_cliente}' no encontrado.")
            if servicio is None:
                raise ParametroFaltanteError(f"Servicio '{id_servicio}' no encontrado.")

            reserva = Reserva(
                id_reserva=id_reserva,
                cliente=cliente,
                servicio=servicio,
                duracion_horas=duracion_horas,
                descuento_pct=descuento_pct,
                impuesto_pct=impuesto_pct,
                **detalle_servicio,
            )
            reserva.confirmar()
            self.reservas.append(reserva)
            return reserva.resumen()
        except ErrorSistemaFJ as exc:
            # Encadenamiento explícito de excepciones
            raise OperacionReservaError(
                f"No fue posible completar la reserva '{id_reserva}'."
            ) from exc


# ==============================================================================
# 7. SIMULACIÓN DE 11 OPERACIONES (ÉXITOS Y ERRORES CONTROLADOS)
# ==============================================================================
def ejecutar_operacion(numero: int, descripcion: str, accion) -> None:
    """Ejecuta una operación con try / except / else / finally y registra en log."""
    print(f"\n--- Operación #{numero}: {descripcion} ---")
    try:
        resultado = accion()
    except ErrorSistemaFJ as err:
        causa = f" | Causa encadenada: {type(err.__cause__).__name__}: {err.__cause__}" if err.__cause__ else ""
        mensaje = f"Op #{numero} FALLIDA [{type(err).__name__}]: {err}{causa}"
        print(f"  [ERROR CONTROLADO] {mensaje}")
        logger.error(mensaje)
    else:
        mensaje = f"Op #{numero} EXITOSA -> {resultado}"
        print(f"  [OK] {mensaje}")
        logger.info(mensaje)
    finally:
        print(f"  [FINALLY] Control de ejecución finalizado para Operación #{numero}.")


def main() -> None:
    gestor = GestorSoftwareFJ()

    # 1. Registro válido de cliente
    ejecutar_operacion(
        1,
        "Registrar cliente válido",
        lambda: gestor.registrar_cliente(
            Cliente("CLI-01", "Laura Gómez", "laura.gomez@softwarefj.com")
        ),
    )

    # 2. Registro inválido de cliente (correo sin formato válido)
    ejecutar_operacion(
        2,
        "Registrar cliente con correo inválido",
        lambda: gestor.registrar_cliente(
            Cliente("CLI-02", "Carlos Ruiz", "carlos_sin_arroba.com")
        ),
    )

    # 3. Registro inválido de cliente (nombre faltante)
    ejecutar_operacion(
        3,
        "Registrar cliente con nombre vacío",
        lambda: gestor.registrar_cliente(
            Cliente("CLI-03", "   ", "valido@softwarefj.com")
        ),
    )

    # 4. Registro válido de servicio ReservaSala
    ejecutar_operacion(
        4,
        "Registrar servicio de Sala",
        lambda: gestor.registrar_servicio(
            ReservaSala("SRV-SALA1", "Sala Ejecutiva A", 45.0, capacidad_maxima=10)
        ),
    )

    # 5. Registro válido de servicio AlquilerEquipo
    ejecutar_operacion(
        5,
        "Registrar servicio de Alquiler de Equipo",
        lambda: gestor.registrar_servicio(
            AlquilerEquipo("SRV-EQ1", "Estación Portátil", 18.0, unidades_disponibles=4)
        ),
    )

    # 6. Registro válido de servicio AsesoriaEspecializada
    ejecutar_operacion(
        6,
        "Registrar servicio de Asesoría Especializada",
        lambda: gestor.registrar_servicio(
            AsesoriaEspecializada("SRV-ASE1", "Consultoría Python & Cloud", 65.0, "Arquitectura")
        ),
    )

    # 7. Creación inválida de servicio (tarifa negativa -> CalculoInconsistenteError)
    ejecutar_operacion(
        7,
        "Crear servicio con tarifa negativa",
        lambda: gestor.registrar_servicio(
            ReservaSala("SRV-ERR", "Sala Inválida", -15.0, capacidad_maxima=6)
        ),
    )

    # 8. Reserva exitosa de Sala con descuento e impuesto
    ejecutar_operacion(
        8,
        "Reserva exitosa de Sala (2h, 6 asistentes, 10% desc, 19% imp)",
        lambda: gestor.crear_y_confirmar_reserva(
            "RES-01",
            "CLI-01",
            "SRV-SALA1",
            duracion_horas=2,
            descuento_pct=10,
            impuesto_pct=19,
            asistentes=6,
        ),
    )

    # 9. Reserva exitosa de Asesoría Especializada (parámetros opcionales por defecto)
    ejecutar_operacion(
        9,
        "Reserva exitosa de Asesoría Especializada (2h)",
        lambda: gestor.crear_y_confirmar_reserva(
            "RES-02",
            "CLI-01",
            "SRV-ASE1",
            duracion_horas=2,
        ),
    )

    # 10. Reserva fallida por exceder unidades disponibles de equipo
    ejecutar_operacion(
        10,
        "Reserva fallida por unidades insuficientes (9 equipos)",
        lambda: gestor.crear_y_confirmar_reserva(
            "RES-03",
            "CLI-01",
            "SRV-EQ1",
            duracion_horas=2,
            unidades=9,
        ),
    )

    # 11. Cancelación de reserva y posterior intento inválido de confirmarla
    def op_cancelar_y_reconfirmar() -> str:
        reserva = gestor.reservas[0]
        reserva.cancelar("Reprogramación solicitada por el cliente")
        reserva.confirmar()  # Provoca OperacionReservaError
        return reserva.resumen()

    ejecutar_operacion(
        11,
        "Cancelar reserva y luego intentar reconfirmarla",
        op_cancelar_y_reconfirmar,
    )

    print("\n=== RESUMEN FINAL EN MEMORIA ===")
    print(f"Clientes registrados: {len(gestor.clientes)}")
    print(f"Servicios registrados: {len(gestor.servicios)}")
    print(f"Reservas creadas: {len(gestor.reservas)}")
    for r in gestor.reservas:
        print(" -", r.resumen())


if __name__ == "__main__":
    main()
