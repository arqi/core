"""Test the Fully Kiosk Browser config flow."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock

from aiohttp.client_exceptions import ClientConnectorError
from fullykiosk import FullyKioskError
import pytest

from homeassistant.components.fully_kiosk.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry


async def test_full_flow(
    hass: HomeAssistant,
    mock_fully_kiosk_config_flow: MagicMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test the full user initiated config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == SOURCE_USER
    assert "flow_id" in result

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "1.1.1.1",
            CONF_PASSWORD: "test-password",
        },
    )

    assert result2.get("type") == FlowResultType.CREATE_ENTRY
    assert result2.get("title") == "Test device"
    assert result2.get("data") == {
        CONF_HOST: "1.1.1.1",
        CONF_PASSWORD: "test-password",
    }
    assert "result" in result2
    assert result2["result"].unique_id == "12345"

    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_fully_kiosk_config_flow.getDeviceInfo.mock_calls) == 1


@pytest.mark.parametrize(
    "side_effect,reason",
    [
        (FullyKioskError("error", "status"), "cannot_connect"),
        (ClientConnectorError(None, Mock()), "cannot_connect"),
        (asyncio.TimeoutError, "cannot_connect"),
        (RuntimeError, "unknown"),
    ],
)
async def test_errors(
    hass: HomeAssistant,
    mock_fully_kiosk_config_flow: MagicMock,
    mock_setup_entry: AsyncMock,
    side_effect: Exception,
    reason: str,
) -> None:
    """Test errors raised during flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert "flow_id" in result
    flow_id = result["flow_id"]

    mock_fully_kiosk_config_flow.getDeviceInfo.side_effect = side_effect
    result2 = await hass.config_entries.flow.async_configure(
        flow_id, user_input={CONF_HOST: "1.1.1.1", CONF_PASSWORD: "test-password"}
    )

    assert result2.get("type") == FlowResultType.FORM
    assert result2.get("step_id") == "user"
    assert result2.get("errors") == {"base": reason}

    assert len(mock_fully_kiosk_config_flow.getDeviceInfo.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 0

    mock_fully_kiosk_config_flow.getDeviceInfo.side_effect = None
    result3 = await hass.config_entries.flow.async_configure(
        flow_id, user_input={CONF_HOST: "1.1.1.1", CONF_PASSWORD: "test-password"}
    )

    assert result3.get("type") == FlowResultType.CREATE_ENTRY
    assert result3.get("title") == "Test device"
    assert result3.get("data") == {
        CONF_HOST: "1.1.1.1",
        CONF_PASSWORD: "test-password",
    }
    assert "result" in result3
    assert result3["result"].unique_id == "12345"

    assert len(mock_fully_kiosk_config_flow.getDeviceInfo.mock_calls) == 2
    assert len(mock_setup_entry.mock_calls) == 1


async def test_duplicate_updates_existing_entry(
    hass: HomeAssistant,
    mock_fully_kiosk_config_flow: MagicMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test adding existing device updates existing entry."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result.get("type") == FlowResultType.FORM
    assert result.get("step_id") == SOURCE_USER
    assert "flow_id" in result

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "1.1.1.1",
            CONF_PASSWORD: "test-password",
        },
    )

    assert result2.get("type") == FlowResultType.ABORT
    assert result2.get("reason") == "already_configured"
    assert mock_config_entry.data == {
        CONF_HOST: "1.1.1.1",
        CONF_PASSWORD: "test-password",
    }

    assert len(mock_fully_kiosk_config_flow.getDeviceInfo.mock_calls) == 1
