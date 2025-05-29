import pytest
from unittest.mock import patch, call, MagicMock
from plc.plc import S7_200, OutputType
from snap7 import Area
import threading


class TestS7200Connection:
    """Test suite for S7_200 connection functionality."""
    
    @patch("plc.plc.snap7.client.Client")
    @patch("plc.plc.os.getenv")
    def test_init_with_explicit_params(self, mock_getenv, mock_client):
        """Test initialization with explicitly provided parameters."""
        # Arrange
        mock_instance = mock_client.return_value
        mock_instance.get_connected.return_value = True
        
        # Act
        plc = S7_200(ip="192.168.1.100", localtsap=0x0100, remotetsap=0x0200)
        
        # Assert
        mock_client.assert_called_once()
        mock_instance.set_connection_type.assert_called_once_with(3)
        mock_instance.set_connection_params.assert_called_once_with("192.168.1.100", 0x0100, 0x0200)
        mock_instance.connect.assert_called_once_with("192.168.1.100", 0, 0)
        mock_instance.get_connected.assert_called_once()
        assert isinstance(plc.lock, threading.Lock)
        # Environment variables should not be called when explicit params provided
        mock_getenv.assert_not_called()

    @patch("plc.plc.snap7.client.Client")
    @patch("plc.plc.os.getenv")
    def test_init_with_env_variables(self, mock_getenv, mock_client):
        """Test initialization using environment variables."""
        # Arrange
        mock_getenv.side_effect = lambda key: {
            "PLC_IP": "192.168.1.50",
            "PLC_LOCALTSAP": "0x0200", 
            "PLC_REMOTETSAP": "0x0300"
        }.get(key)
        mock_instance = mock_client.return_value
        mock_instance.get_connected.return_value = True
        
        # Act
        plc = S7_200()
        
        # Assert
        expected_calls = [call("PLC_IP"), call("PLC_LOCALTSAP"), call("PLC_REMOTETSAP")]
        mock_getenv.assert_has_calls(expected_calls)
        mock_instance.set_connection_params.assert_called_once_with("192.168.1.50", 0x0200, 0x0300)
        mock_instance.connect.assert_called_once_with("192.168.1.50", 0, 0)

    @patch("plc.plc.snap7.client.Client")
    def test_connection_failure(self, mock_client):
        """Test handling of connection failures."""
        # Arrange
        mock_instance = mock_client.return_value
        mock_instance.connect.side_effect = Exception("Connection timeout")
        mock_instance.get_connected.return_value = False
        
        # Act - should not raise exception
        plc = S7_200(ip="192.168.1.100", localtsap=0x0100, remotetsap=0x0200)
        
        # Assert
        mock_instance.connect.assert_called_once()
        assert plc.plc == mock_instance

    @patch("plc.plc.snap7.client.Client")
    def test_successful_connection_message(self, mock_client):
        """Test successful connection prints correct message."""
        # Arrange
        mock_instance = mock_client.return_value
        mock_instance.get_connected.return_value = True
        
        # Act & Assert - we can't easily test print statements, but we can verify the flow
        plc = S7_200(ip="192.168.1.100", localtsap=0x0100, remotetsap=0x0200)
        mock_instance.get_connected.assert_called_once()

    @patch("plc.plc.snap7.client.Client")
    def test_disconnect(self, mock_client):
        """Test PLC disconnection."""
        # Arrange
        mock_instance = mock_client.return_value
        mock_instance.get_connected.return_value = True
        plc = S7_200(ip="192.168.1.100", localtsap=0x0100, remotetsap=0x0200)
        
        # Act
        plc.disconnect()
        
        # Assert
        mock_instance.disconnect.assert_called_once()


class TestMemoryAddressTranslation:
    """Test suite for memory address translation functionality."""
    
    def test_translate_alias_m_memory(self):
        """Test translation of M-memory aliases."""
        plc = S7_200.__new__(S7_200)  # Create instance without calling __init__
        plc.logger = MagicMock()  # Mock the logger
        
        # Test various M-memory formats
        assert plc._translate_alias("M1.0") == "VX1.0"
        assert plc._translate_alias("m10.7") == "VX10.7"
        assert plc._translate_alias("M255.3") == "VX255.3"

    def test_translate_alias_vd_memory(self):
        """Test translation of VD-memory aliases."""
        plc = S7_200.__new__(S7_200)
        plc.logger = MagicMock()  # Mock the logger
        
        assert plc._translate_alias("VD100") == "DB1.DBD100"
        assert plc._translate_alias("vd0") == "DB1.DBD0"
        assert plc._translate_alias("VD1000") == "DB1.DBD1000"

    def test_translate_alias_vw_memory(self):
        """Test translation of VW-memory aliases."""
        plc = S7_200.__new__(S7_200)
        plc.logger = MagicMock()  # Mock the logger
        
        assert plc._translate_alias("VW50") == "DB1.DBW50"
        assert plc._translate_alias("vw0") == "DB1.DBW0"
        assert plc._translate_alias("VW200") == "DB1.DBW200"

    def test_translate_alias_passthrough(self):
        """Test that non-aliased addresses pass through unchanged."""
        plc = S7_200.__new__(S7_200)
        plc.logger = MagicMock()  # Mock the logger
        
        test_addresses = ["DB1.DBX0.0", "QX0.1", "IX1.0", "VX10.5", "random_string"]
        for addr in test_addresses:
            assert plc._translate_alias(addr) == addr.upper()


class TestMemoryAreaResolution:
    """Test suite for memory area resolution functionality."""
    
    def test_resolve_area_db(self):
        """Test DB area resolution."""
        plc = S7_200.__new__(S7_200)
        plc.logger = MagicMock()  # Mock the logger
        
        assert plc._resolve_area("db1.dbx0.0") == Area.DB
        assert plc._resolve_area("DB10.DBW100") == Area.DB

    def test_resolve_area_pe(self):
        """Test PE (Process Input) area resolution."""
        plc = S7_200.__new__(S7_200)
        plc.logger = MagicMock()  # Mock the logger
        
        assert plc._resolve_area("aiw0") == Area.PE
        assert plc._resolve_area("iw10") == Area.PE
        assert plc._resolve_area("ix0.0") == Area.PE
        assert plc._resolve_area("ib5") == Area.PE

    def test_resolve_area_pa(self):
        """Test PA (Process Output) area resolution."""
        plc = S7_200.__new__(S7_200)
        plc.logger = MagicMock()  # Mock the logger
        
        assert plc._resolve_area("aqw0") == Area.PA
        assert plc._resolve_area("qw10") == Area.PA
        assert plc._resolve_area("qx0.0") == Area.PA
        assert plc._resolve_area("qb5") == Area.PA

    def test_resolve_area_mk(self):
        """Test MK (Marker/Memory) area resolution."""
        plc = S7_200.__new__(S7_200)
        plc.logger = MagicMock()  # Mock the logger
        
        assert plc._resolve_area("vx0.0") == Area.MK
        assert plc._resolve_area("vw100") == Area.MK
        assert plc._resolve_area("mx1.0") == Area.MK
        assert plc._resolve_area("mb10") == Area.MK

    def test_resolve_area_unknown(self):
        """Test error handling for unknown memory areas."""
        plc = S7_200.__new__(S7_200)
        plc.logger = MagicMock()  # Mock the logger
        
        with pytest.raises(ValueError, match="Unknown memory area for 'unknown'"):
            plc._resolve_area("unknown")
        
        with pytest.raises(ValueError, match="Unknown memory area for 'xyz123'"):
            plc._resolve_area("xyz123")


class TestMemoryReading:
    """Test suite for memory reading functionality."""
    
    @patch("plc.plc.snap7.client.Client")
    def test_get_mem_bool_vx_area(self, mock_client):
        """Test reading boolean values from VX area (not DB)."""
        # Arrange
        mock_instance = mock_client.return_value
        mock_instance.get_connected.return_value = True
        mock_instance.read_area.return_value = bytearray([0x01])  # Bit pattern: 00000001
        
        with patch("plc.plc.get_bool", return_value=True) as mock_get_bool:
            plc = S7_200(ip="192.168.1.100", localtsap=0x0100, remotetsap=0x0200)
            
            # Act
            result = plc.getMem("VX0.0")
            
            # Assert
            mock_instance.read_area.assert_called_with(Area.MK, 0, 0, 1)
            mock_get_bool.assert_called_once_with(bytearray([0x01]), 0, 0)
            assert result is True

    @patch("plc.plc.snap7.client.Client") 
    def test_get_mem_int_db_area(self, mock_client):
        """Test reading integer values from DB area."""
        # Arrange
        mock_instance = mock_client.return_value
        mock_instance.get_connected.return_value = True
        mock_instance.read_area.return_value = bytearray([0x01, 0x00])  # 256 in big-endian
        
        with patch("plc.plc.get_int", return_value=256) as mock_get_int:
            plc = S7_200(ip="192.168.1.100", localtsap=0x0100, remotetsap=0x0200)
            
            # Act
            result = plc.getMem("DB1.DBW0")
            
            # Assert
            mock_instance.read_area.assert_called_with(Area.DB, 1, 0, 2)
            mock_get_int.assert_called_once_with(bytearray([0x01, 0x00]), 0)
            assert result == 256

    @patch("plc.plc.snap7.client.Client")
    def test_get_mem_real_vd_area(self, mock_client):
        """Test reading real (float) values from VD area (translated to DB)."""
        # Arrange
        mock_instance = mock_client.return_value
        mock_instance.get_connected.return_value = True
        mock_instance.read_area.return_value = bytearray([0x42, 0x28, 0x00, 0x00])  # 42.0 in IEEE 754
        
        with patch("plc.plc.get_real", return_value=42.0) as mock_get_real:
            plc = S7_200(ip="192.168.1.100", localtsap=0x0100, remotetsap=0x0200)
            
            # Act - VD100 gets translated to DB1.DBD100
            result = plc.getMem("VD100")
            
            # Assert - Should be DB area due to translation
            mock_instance.read_area.assert_called_with(Area.DB, 1, 100, 4)
            mock_get_real.assert_called_once_with(bytearray([0x42, 0x28, 0x00, 0x00]), 0)
            assert result == 42.0

    @patch("plc.plc.snap7.client.Client")
    def test_get_mem_return_bytes(self, mock_client):
        """Test reading raw bytes when returnByte=True."""
        # Arrange
        mock_instance = mock_client.return_value
        mock_instance.get_connected.return_value = True
        mock_instance.read_area.return_value = bytearray([0x01, 0x02, 0x03, 0x04])
        
        plc = S7_200(ip="192.168.1.100", localtsap=0x0100, remotetsap=0x0200)
        
        # Act
        result = plc.getMem("VW100", returnByte=True)
        
        # Assert
        assert result == bytearray([0x01, 0x02, 0x03, 0x04])

    @patch("plc.plc.snap7.client.Client")
    def test_get_mem_uses_lock(self, mock_client):
        """Test that getMem uses threading lock (indirect test)."""
        # Arrange
        mock_instance = mock_client.return_value
        mock_instance.get_connected.return_value = True
        mock_instance.read_area.return_value = bytearray([0x01])
        
        plc = S7_200(ip="192.168.1.100", localtsap=0x0100, remotetsap=0x0200)
        
        # Replace lock with mock
        mock_lock = MagicMock()
        plc.lock = mock_lock
        
        # Act
        plc.getMem("VX0.0")
        
        # Assert
        mock_lock.__enter__.assert_called_once()
        mock_lock.__exit__.assert_called_once()


class TestMemoryWriting:
    """Test suite for memory writing functionality."""
    
    @patch("plc.plc.snap7.client.Client")
    def test_write_mem_bool_vx_area(self, mock_client):
        """Test writing boolean values to VX area."""
        # Arrange
        mock_instance = mock_client.return_value
        mock_instance.get_connected.return_value = True
        mock_instance.read_area.return_value = bytearray([0x00])
        mock_instance.write_area.return_value = 0  # Success
        
        with patch("plc.plc.set_bool") as mock_set_bool:
            plc = S7_200(ip="192.168.1.100", localtsap=0x0100, remotetsap=0x0200)
            
            # Act
            result = plc.writeMem("VX0.0", True)
            
            # Assert
            mock_instance.read_area.assert_called_with(Area.MK, 0, 0, 1)
            mock_set_bool.assert_called_once_with(bytearray([0x00]), 0, 0, 1)  # True converted to 1
            mock_instance.write_area.assert_called_once_with(Area.MK, 0, 0, bytearray([0x00]))
            assert result == 0

    @patch("plc.plc.snap7.client.Client")
    def test_write_mem_int_db_area(self, mock_client):
        """Test writing integer values to DB area."""
        # Arrange
        mock_instance = mock_client.return_value
        mock_instance.get_connected.return_value = True
        mock_instance.read_area.return_value = bytearray([0x00, 0x00])
        mock_instance.write_area.return_value = 0
        
        with patch("plc.plc.set_int") as mock_set_int:
            plc = S7_200(ip="192.168.1.100", localtsap=0x0100, remotetsap=0x0200)
            
            # Act
            result = plc.writeMem("DB1.DBW0", 1234)
            
            # Assert
            mock_set_int.assert_called_once_with(bytearray([0x00, 0x00]), 0, 1234)
            mock_instance.write_area.assert_called_once_with(Area.DB, 1, 0, bytearray([0x00, 0x00]))

    @patch("plc.plc.snap7.client.Client")
    def test_write_mem_real_db_area(self, mock_client):
        """Test writing real (float) values to DB area."""
        # Arrange
        mock_instance = mock_client.return_value
        mock_instance.get_connected.return_value = True
        mock_instance.read_area.return_value = bytearray([0x00, 0x00, 0x00, 0x00])
        mock_instance.write_area.return_value = 0
        
        with patch("plc.plc.set_real") as mock_set_real:
            plc = S7_200(ip="192.168.1.100", localtsap=0x0100, remotetsap=0x0200)
            
            # Act
            result = plc.writeMem("DB1.DBD0", 3.14159)
            
            # Assert
            mock_set_real.assert_called_once_with(bytearray([0x00, 0x00, 0x00, 0x00]), 0, 3.14159)

    @patch("plc.plc.snap7.client.Client")
    def test_write_mem_with_time_delay(self, mock_client):
        """Test that writeMem includes proper time delay."""
        # Arrange
        mock_instance = mock_client.return_value
        mock_instance.get_connected.return_value = True
        mock_instance.read_area.return_value = bytearray([0x00])
        mock_instance.write_area.return_value = 0
        
        with patch("plc.plc.time.sleep") as mock_sleep:
            plc = S7_200(ip="192.168.1.100", localtsap=0x0100, remotetsap=0x0200)
            
            # Act
            plc.writeMem("VX0.0", True)
            
            # Assert
            mock_sleep.assert_called_once_with(0.05)

    @patch("plc.plc.snap7.client.Client")
    def test_write_mem_uses_lock(self, mock_client):
        """Test that writeMem uses threading lock (indirect test)."""
        # Arrange
        mock_instance = mock_client.return_value
        mock_instance.get_connected.return_value = True
        mock_instance.read_area.return_value = bytearray([0x00])
        mock_instance.write_area.return_value = 0
        
        plc = S7_200(ip="192.168.1.100", localtsap=0x0100, remotetsap=0x0200)
        
        # Replace lock with mock
        mock_lock = MagicMock()
        plc.lock = mock_lock
        
        # Act
        plc.writeMem("VX0.0", True)
        
        # Assert - writeMem calls getMem first (1 lock) then write operation (1 lock) = 2 total
        assert mock_lock.__enter__.call_count == 2
        assert mock_lock.__exit__.call_count == 2


class TestParameterizedMemoryOperations:
    """Parameterized tests for various memory address formats."""
    
    @pytest.mark.parametrize("address,expected_area,expected_db,expected_start,expected_length", [
        ("DB2.DBW100", Area.DB, 2, 100, 2), 
        ("DB3.DBD200", Area.DB, 3, 200, 4),
        ("VX10.5", Area.MK, 0, 10, 1),
        ("QX0.0", Area.PA, 0, 0, 1),
        ("IW10", Area.PE, 0, 10, 2),
        # Note: VW50 and VD100 get translated to DB area due to alias translation
        ("VW50", Area.DB, 1, 50, 2),  # VW gets translated to DB1.DBW
        ("VD100", Area.DB, 1, 100, 4), # VD gets translated to DB1.DBD
    ])
    @patch("plc.plc.snap7.client.Client")
    def test_memory_address_parsing(self, mock_client, address, expected_area, expected_db, expected_start, expected_length):
        """Test that various memory addresses are parsed correctly."""
        # Arrange
        mock_instance = mock_client.return_value
        mock_instance.get_connected.return_value = True
        mock_instance.read_area.return_value = bytearray(b'\x00' * expected_length)
        
        plc = S7_200(ip="192.168.1.100", localtsap=0x0100, remotetsap=0x0200)
        
        # Act
        plc.getMem(address, returnByte=True)
        
        # Assert
        mock_instance.read_area.assert_called_with(expected_area, expected_db, expected_start, expected_length)


class TestErrorHandling:
    """Test suite for error handling scenarios."""
    
    def test_resolve_area_invalid_address(self):
        """Test error handling for invalid memory addresses."""
        plc = S7_200.__new__(S7_200)
        plc.logger = MagicMock()  # Mock the logger

        # Test with an address that doesn't match any pattern
        with pytest.raises(ValueError, match="Unknown memory area"):
            plc._resolve_area("xyz123")
    
    @patch("plc.plc.snap7.client.Client")
    def test_connection_with_invalid_env_vars(self, mock_client):
        """Test handling of invalid environment variables."""
        mock_instance = mock_client.return_value
        mock_instance.get_connected.return_value = True
        
        with patch("plc.plc.os.getenv") as mock_getenv:
            # Simulate missing environment variables
            mock_getenv.return_value = None
            
            # This should handle None values gracefully
            with pytest.raises(TypeError):  # int() of None will raise TypeError
                S7_200()


class TestOutputTypeConstants:
    """Test suite for OutputType constants."""
    
    def test_output_type_values(self):
        """Test that OutputType constants have expected values."""
        assert OutputType.BOOL == 1
        assert OutputType.INT == 2
        assert OutputType.REAL == 3
        assert OutputType.DWORD == 4


if __name__ == "__main__":
    pytest.main([__file__]) 