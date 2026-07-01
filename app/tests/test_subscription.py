"""
Tests para SubscriptionService - trial y seleccion de plan
"""

from services import SubscriptionService


class TestSubscriptionService:
    def test_crea_trial_inicial_cuando_no_existe(self, db_manager):
        service = SubscriptionService(db_manager)

        estado = service.obtener_estado_trial(usuario_id=1, primera_sesion=True)

        assert estado['es_primer_inicio'] is True
        assert estado['plan_seleccionado'] is False
        assert estado['trial_activo'] is True
        assert estado['dias_restantes'] == 30
        assert estado['suscripcion'] is not None

    def test_seleccionar_plan_guarda_datos(self, db_manager):
        service = SubscriptionService(db_manager)
        service.crear_trial_inicial(usuario_id=1)

        ok, msg = service.seleccionar_plan('pro', usuario_id=1)
        suscripcion = service.obtener_suscripcion()

        assert ok is True
        assert 'PRO' in msg
        assert suscripcion['plan_codigo'] == 'pro'
        assert suscripcion['plan_nombre'] == 'Plan PRO'
        assert float(suscripcion['plan_precio_mensual']) == 20.0

    def test_cuenta_existente_sin_suscripcion_no_marca_primer_inicio(self, db_manager):
        service = SubscriptionService(db_manager)

        estado = service.obtener_estado_trial(usuario_id=1, primera_sesion=False)

        assert estado['es_primer_inicio'] is False
        assert estado['trial_activo'] is True
        assert estado['plan_seleccionado'] is False
