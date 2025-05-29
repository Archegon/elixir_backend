from unittest.mock import patch
from modules.plc import S7_200

@patch("modules.plc.snap7.client.Client")
def test_plc_connect(mock_client):
    # Arrange
    mock_instance = mock_client.return_value
    mock_instance.get_connected.return_value = True

    # Act
    S7_200(ip="192.168.2.1", localtsap=0x0100, remotetsap=0x0200)

    # Assert
    mock_instance.connect.assert_called_with("192.168.2.1", 0, 0)
    assert mock_instance.get_connected.called

@patch("modules.plc.snap7.client.Client")
def test_plc_disconnect(mock_client):
    mock_instance = mock_client.return_value
    plc = S7_200(ip="192.168.2.1", localtsap=0x0100, remotetsap=0x0200)
    plc.disconnect()
    mock_instance.disconnect.assert_called_once() 