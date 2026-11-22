import logging

from app.main import create_app


def test_access_log_has_no_query_string(client, caplog):
    caplog.set_level(logging.INFO, logger="garbagego.access")
    client.get("/health?lat=24.123456&lon=120.654321")
    assert "/health" in caplog.text
    assert "24.123456" not in caplog.text and "120.654321" not in caplog.text


def test_access_logger_emits_info_outside_pytest():
    # uvicorn runs with --no-access-log and does not configure our logger,
    # so the app itself must attach a handler at INFO or nothing is printed.
    create_app()
    create_app()
    logger = logging.getLogger("garbagego.access")
    assert logger.isEnabledFor(logging.INFO)
    assert len(logger.handlers) == 1
