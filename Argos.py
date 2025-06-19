import asyncio
import aiofiles
import json
import yaml
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Any, AsyncGenerator, Union
import logging
import os
import subprocess
from datetime import datetime

# Configuration Management
@dataclass
class ArgosConfig:
    """Configuration class for Argos framework"""
    # Network settings
    interfaces: List[str] = field(default_factory=list)
    bridge_name: Optional[str] = None
    promiscuous_mode: bool = True
    
    # Capture settings
    default_filter: str = ""
    default_count: int = 100
    default_timeout: int = 30
    capture_buffer_size: int = 1024 * 1024  # 1MB
    
    # Async settings
    max_concurrent_captures: int = 5
    executor_type: str = "thread"  # "thread" or "process"
    max_workers: Optional[int] = None
    
    # Logging settings
    log_level: str = "INFO"
    log_file: Optional[str] = None
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Output settings
    output_format: str = "json"  # "json", "yaml", "csv"
    output_directory: str = "./captures"
    
    # Protocol-specific settings
    protocol_settings: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    async def from_file(cls, config_path: Union[str, Path]) -> 'ArgosConfig':
        """Load configuration from file (JSON or YAML)"""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        async with aiofiles.open(config_path, 'r') as f:
            content = await f.read()
        
        if config_path.suffix.lower() in ['.yaml', '.yml']:
            data = yaml.safe_load(content)
        else:
            data = json.loads(content)
        
        return cls(**data)
    
    @classmethod
    def from_env(cls) -> 'ArgosConfig':
        """Load configuration from environment variables"""
        config = cls()
        
        # Network settings
        if interfaces := os.getenv('ARGOS_INTERFACES'):
            config.interfaces = interfaces.split(',')
        if bridge := os.getenv('ARGOS_BRIDGE_NAME'):
            config.bridge_name = bridge
        
        # Capture settings
        if filter_expr := os.getenv('ARGOS_DEFAULT_FILTER'):
            config.default_filter = filter_expr
        if count := os.getenv('ARGOS_DEFAULT_COUNT'):
            config.default_count = int(count)
        if timeout := os.getenv('ARGOS_DEFAULT_TIMEOUT'):
            config.default_timeout = int(timeout)
        
        # Async settings
        if max_concurrent := os.getenv('ARGOS_MAX_CONCURRENT'):
            config.max_concurrent_captures = int(max_concurrent)
        if executor := os.getenv('ARGOS_EXECUTOR_TYPE'):
            config.executor_type = executor
        
        # Logging
        if log_level := os.getenv('ARGOS_LOG_LEVEL'):
            config.log_level = log_level
        if log_file := os.getenv('ARGOS_LOG_FILE'):
            config.log_file = log_file
        
        return config
    
    async def save_to_file(self, config_path: Union[str, Path]):
        """Save configuration to file"""
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'interfaces': self.interfaces,
            'bridge_name': self.bridge_name,
            'promiscuous_mode': self.promiscuous_mode,
            'default_filter': self.default_filter,
            'default_count': self.default_count,
            'default_timeout': self.default_timeout,
            'max_concurrent_captures': self.max_concurrent_captures,
            'executor_type': self.executor_type,
            'max_workers': self.max_workers,
            'log_level': self.log_level,
            'log_file': self.log_file,
            'output_format': self.output_format,
            'output_directory': self.output_directory,
            'protocol_settings': self.protocol_settings
        }
        
        async with aiofiles.open(config_path, 'w') as f:
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                await f.write(yaml.dump(data, default_flow_style=False))
            else:
                await f.write(json.dumps(data, indent=2))


class ArgosError(Exception):
    """Base exception for Argos operations"""
    pass

class InterfaceError(ArgosError):
    """Interface-related errors"""
    pass

class BridgeError(ArgosError):
    """Bridge-related errors"""
    pass

class CaptureError(ArgosError):
    """Capture-related errors"""
    pass


class AsyncArgosBase(ABC):
    """Async version of ArgosBase with configuration management"""
    
    def __init__(self, config: Optional[ArgosConfig] = None):
        self.config = config or ArgosConfig()
        self.logger = self._setup_logging()
        self.executor = self._setup_executor()
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_captures)
        self._capture_tasks: List[asyncio.Task] = []
        
        # Ensure output directory exists
        Path(self.config.output_directory).mkdir(parents=True, exist_ok=True)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup async-compatible logging"""
        logger = logging.getLogger(f"{self.__class__.__name__}")
        logger.setLevel(getattr(logging, self.config.log_level.upper()))
        
        if not logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter(self.config.log_format)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            # File handler if specified
            if self.config.log_file:
                file_handler = logging.FileHandler(self.config.log_file)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
        
        return logger
    
    def _setup_executor(self):
        """Setup executor for blocking operations"""
        if self.config.executor_type.lower() == "process":
            return ProcessPoolExecutor(max_workers=self.config.max_workers)
        else:
            return ThreadPoolExecutor(max_workers=self.config.max_workers)
    
    async def _run_command_async(self, cmd: List[str], error_msg: str = "Command failed") -> str:
        """Execute system command asynchronously"""
        try:
            self.logger.debug(f"Executing async: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error = stderr.decode() if stderr else "Unknown error"
                self.logger.error(f"{error_msg}: {error}")
                raise ArgosError(f"{error_msg}: {error}")
            
            return stdout.decode()
            
        except FileNotFoundError as e:
            raise ArgosError(f"Command not found: {cmd[0]}") from e
    
    async def _interface_exists(self, iface: str) -> bool:
        """Check if network interface exists asynchronously"""
        return await asyncio.get_event_loop().run_in_executor(
            None, os.path.exists, f"/sys/class/net/{iface}"
        )
    
    async def validate_interfaces(self):
        """Validate all configured interfaces"""
        for iface in self.config.interfaces:
            if not await self._interface_exists(iface):
                raise InterfaceError(f"Interface {iface} does not exist")
    
    async def bring_up(self, iface: str):
        """Bring network interface up asynchronously"""
        if not await self._interface_exists(iface):
            raise InterfaceError(f"Interface {iface} does not exist")
        
        cmd = ["ip", "link", "set", iface, "up"]
        if self.config.promiscuous_mode:
            cmd.append("promisc")
            cmd.append("on")
        
        await self._run_command_async(cmd, f"Failed to bring up interface {iface}")
        self.logger.info(f"Interface {iface} brought up successfully")
    
    async def bring_down(self, iface: str):
        """Bring network interface down asynchronously"""
        if not await self._interface_exists(iface):
            raise InterfaceError(f"Interface {iface} does not exist")
        
        await self._run_command_async(
            ["ip", "link", "set", iface, "down"],
            f"Failed to bring down interface {iface}"
        )
        self.logger.info(f"Interface {iface} brought down successfully")
    
    async def create_bridge(self):
        """Create bridge and add interfaces asynchronously"""
        if not self.config.bridge_name:
            raise BridgeError("No bridge name configured")
        
        try:
            # Create bridge
            await self._run_command_async(
                ["ip", "link", "add", self.config.bridge_name, "type", "bridge"],
                f"Failed to create bridge {self.config.bridge_name}"
            )
            
            # Add interfaces to bridge concurrently
            tasks = []
            for iface in self.config.interfaces:
                task = self._run_command_async(
                    ["ip", "link", "set", iface, "master", self.config.bridge_name],
                    f"Failed to add {iface} to bridge {self.config.bridge_name}"
                )
                tasks.append(task)
            
            await asyncio.gather(*tasks)
            
            # Bring up bridge
            await self.bring_up(self.config.bridge_name)
            self.logger.info(f"Bridge {self.config.bridge_name} created with interfaces: {self.config.interfaces}")
            
        except ArgosError:
            await self._cleanup_bridge()
            raise
    
    async def destroy_bridge(self):
        """Destroy bridge asynchronously"""
        if not self.config.bridge_name:
            return
        
        try:
            await self.bring_down(self.config.bridge_name)
            await self._run_command_async(
                ["ip", "link", "delete", self.config.bridge_name, "type", "bridge"],
                f"Failed to delete bridge {self.config.bridge_name}"
            )
            self.logger.info(f"Bridge {self.config.bridge_name} destroyed")
        except ArgosError as e:
            self.logger.warning(f"Error destroying bridge: {e}")
    
    async def _cleanup_bridge(self):
        """Internal cleanup method"""
        try:
            await self.destroy_bridge()
        except Exception as e:
            self.logger.warning(f"Cleanup failed: {e}")
    
    @asynccontextmanager
    async def bridge_context(self):
        """Async context manager for bridge lifecycle"""
        if self.config.bridge_name:
            try:
                await self.create_bridge()
                yield self
            finally:
                await self.destroy_bridge()
        else:
            yield self
    
    async def capture_single(self, iface: str, filter_expr: Optional[str] = None, 
                           count: Optional[int] = None, timeout: Optional[int] = None) -> List[Any]:
        """Capture packets on a single interface"""
        async with self._semaphore:  # Limit concurrent captures
            if not await self._interface_exists(iface):
                raise InterfaceError(f"Interface {iface} does not exist")
            
            filter_expr = filter_expr or self.config.default_filter
            count = count or self.config.default_count
            timeout = timeout or self.config.default_timeout
            
            self.logger.info(f"Starting capture on {iface} with filter: '{filter_expr}'")
            
            try:
                # Run packet capture in executor to avoid blocking
                packets = await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    self._capture_packets_sync,
                    iface, filter_expr, count, timeout
                )
                
                self.logger.info(f"Captured {len(packets)} packets on {iface}")
                return packets
                
            except Exception as e:
                raise CaptureError(f"Packet capture failed on {iface}: {e}")
    
    def _capture_packets_sync(self, iface: str, filter_expr: str, count: int, timeout: int):
        """Synchronous packet capture for executor"""
        try:
            from scapy.all import sniff
            return sniff(
                iface=iface,
                filter=filter_expr,
                count=count,
                timeout=timeout,
                store=True
            )
        except ImportError:
            raise CaptureError("Scapy not installed. Please install with: pip install scapy")
    
    async def capture_multiple(self, interfaces: Optional[List[str]] = None, 
                             filter_expr: Optional[str] = None,
                             count: Optional[int] = None, 
                             timeout: Optional[int] = None) -> Dict[str, List[Any]]:
        """Capture packets on multiple interfaces concurrently"""
        interfaces = interfaces or self.config.interfaces
        
        if not interfaces:
            raise CaptureError("No interfaces specified for capture")
        
        # Create capture tasks for all interfaces
        tasks = {}
        for iface in interfaces:
            task = asyncio.create_task(
                self.capture_single(iface, filter_expr, count, timeout),
                name=f"capture_{iface}"
            )
            tasks[iface] = task
            self._capture_tasks.append(task)
        
        # Wait for all captures to complete
        results = {}
        completed_tasks = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        for iface, result in zip(interfaces, completed_tasks):
            if isinstance(result, Exception):
                self.logger.error(f"Capture failed on {iface}: {result}")
                results[iface] = []
            else:
                results[iface] = result
        
        return results
    
    async def capture_continuous(self, interfaces: Optional[List[str]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Continuous packet capture with async generator"""
        interfaces = interfaces or self.config.interfaces
        
        while True:
            try:
                results = await self.capture_multiple(interfaces, count=10, timeout=5)
                
                for iface, packets in results.items():
                    if packets:
                        extracted = await self.extract_info_async(packets)
                        yield {
                            'interface': iface,
                            'timestamp': datetime.now().isoformat(),
                            'packets': extracted
                        }
                
                await asyncio.sleep(1)  # Brief pause between captures
                
            except asyncio.CancelledError:
                self.logger.info("Continuous capture cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error in continuous capture: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def extract_info_async(self, packets) -> List[Dict[str, Any]]:
        """Async wrapper for extract_info"""
        return await asyncio.get_event_loop().run_in_executor(
            self.executor,
            self.extract_info,
            packets
        )
    
    @abstractmethod
    def extract_info(self, packets) -> List[Dict[str, Any]]:
        """Extract protocol-specific information from packets (sync method)"""
        pass
    
    async def save_results(self, results: Dict[str, Any], filename: Optional[str] = None):
        """Save capture results to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{timestamp}.{self.config.output_format}"
        
        filepath = Path(self.config.output_directory) / filename
        
        async with aiofiles.open(filepath, 'w') as f:
            if self.config.output_format.lower() == 'yaml':
                await f.write(yaml.dump(results, default_flow_style=False))
            else:
                await f.write(json.dumps(results, indent=2, default=str))
        
        self.logger.info(f"Results saved to {filepath}")
    
    async def cancel_all_captures(self):
        """Cancel all running capture tasks"""
        for task in self._capture_tasks:
            if not task.done():
                task.cancel()
        
        if self._capture_tasks:
            await asyncio.gather(*self._capture_tasks, return_exceptions=True)
        
        self._capture_tasks.clear()
        self.logger.info("All capture tasks cancelled")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.validate_interfaces()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cancel_all_captures()
        self.executor.shutdown(wait=True)


# Enhanced ARP Handler with async support
class AsyncArgosARP(AsyncArgosBase):
    def extract_info(self, packets) -> List[Dict[str, Any]]:
        """Extract ARP information from packets (sync method for executor)"""
        arp_info = []
        
        try:
            from scapy.all import ARP
            
            for pkt in packets:
                if pkt.haslayer(ARP):
                    arp_data = {
                        'timestamp': float(pkt.time),
                        'src_ip': pkt[ARP].psrc,
                        'dst_ip': pkt[ARP].pdst,
                        'src_mac': pkt[ARP].hwsrc,
                        'dst_mac': pkt[ARP].hwdst,
                        'operation': 'request' if pkt[ARP].op == 1 else 'reply'
                    }
                    arp_info.append(arp_data)
            
            return arp_info
            
        except ImportError:
            raise CaptureError("Scapy not installed")


# Usage examples
async def example_usage():
    """Example usage of async Argos with configuration"""
    
    # Load configuration from file or use environment variables
    try:
        config = await ArgosConfig.from_file("argos_config.yaml")
    except FileNotFoundError:
        config = ArgosConfig.from_env()
        config.interfaces = ["eth0", "wlan0"]  # Fallback interfaces
    
    # Create ARP probe with configuration
    async with AsyncArgosARP(config) as arp_probe:
        # Example 1: Single interface capture
        packets = await arp_probe.capture_single("eth0", "arp", count=5)
        arp_data = await arp_probe.extract_info_async(packets)
        print(f"Single capture: {len(arp_data)} ARP packets")
        
        # Example 2: Multiple interface capture
        results = await arp_probe.capture_multiple(["eth0", "wlan0"], "arp", count=10)
        for iface, packets in results.items():
            arp_data = await arp_probe.extract_info_async(packets)
            print(f"{iface}: {len(arp_data)} ARP packets")
        
        # Example 3: Continuous capture with timeout
        async def continuous_with_timeout():
            async for data in arp_probe.capture_continuous():
                print(f"Continuous: {data['interface']} - {len(data['packets'])} packets")
        
        # Run continuous capture for 30 seconds
        try:
            await asyncio.wait_for(continuous_with_timeout(), timeout=30)
        except asyncio.TimeoutError:
            print("Continuous capture completed")


if __name__ == "__main__":
    asyncio.run(example_usage())