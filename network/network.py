"""
network.py
局域网联机模块 / LAN Multiplayer Module
"""

import socket
import pickle
import threading
import time


class NetworkClient:
    """网络客户端 - 用于连接到主机 / Network Client - Connect to host"""
    
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        self.player_id = None  # 1 or 2
        self.received_data = None
        self.lock = threading.Lock()
        
    def connect(self, host, port=5555):
        """连接到主机 / Connect to host"""
        try:
            self.client.connect((host, port))
            self.connected = True
            # 接收玩家ID
            self.player_id = int(self.receive())
            print(f"已连接到主机，你是玩家{self.player_id} / Connected to host, you are player {self.player_id}")
            
            # 启动接收线程
            threading.Thread(target=self._receive_loop, daemon=True).start()
            return True
        except Exception as e:
            print(f"连接失败: {e} / Connection failed: {e}")
            return False
    
    def send(self, data):
        """发送数据 / Send data"""
        try:
            serialized = pickle.dumps(data)
            self.client.sendall(serialized)
            return True
        except Exception as e:
            print(f"发送失败: {e} / Send failed: {e}")
            self.connected = False
            return False
    
    def receive(self):
        """接收数据（阻塞） / Receive data (blocking)"""
        try:
            data = self.client.recv(4096)
            return pickle.loads(data)
        except Exception as e:
            print(f"接收失败: {e} / Receive failed: {e}")
            self.connected = False
            return None
    
    def _receive_loop(self):
        """后台接收循环 / Background receive loop"""
        while self.connected:
            try:
                data = self.client.recv(4096)
                if data:
                    with self.lock:
                        self.received_data = pickle.loads(data)
            except:
                self.connected = False
                break
    
    def get_received_data(self):
        """获取接收到的数据 / Get received data"""
        with self.lock:
            data = self.received_data
            self.received_data = None
            return data
    
    def close(self):
        """关闭连接 / Close connection"""
        self.connected = False
        try:
            self.client.close()
        except:
            pass


class NetworkServer:
    """网络服务器 - 主机玩家使用 / Network Server - Used by host player"""
    
    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connections = []
        self.running = False
        self.client_data = {}  # {player_id: data}
        self.lock = threading.Lock()
        
    def start(self, port=5555):
        """启动服务器 / Start server"""
        try:
            # 获取本机IP
            local_ip = get_local_ip()
            
            self.server.bind(('0.0.0.0', port))
            self.server.listen(1)  # 只接受1个客户端（2人游戏）
            self.running = True
            
            print(f"服务器已启动 / Server started")
            print(f"本机IP: {local_ip}")
            print(f"端口: {port}")
            print(f"等待玩家2连接... / Waiting for player 2...")
            
            # 启动接受连接的线程
            threading.Thread(target=self._accept_connections, daemon=True).start()
            return local_ip, port
        except Exception as e:
            print(f"启动服务器失败: {e} / Failed to start server: {e}")
            return None, None
    
    def _accept_connections(self):
        """接受客户端连接 / Accept client connections"""
        while self.running and len(self.connections) < 1:
            try:
                conn, addr = self.server.accept()
                print(f"玩家2已连接: {addr} / Player 2 connected: {addr}")
                
                # 发送玩家ID
                conn.sendall(pickle.dumps(2))
                
                self.connections.append(conn)
                
                # 启动接收线程
                threading.Thread(target=self._receive_from_client, 
                               args=(conn, 2), daemon=True).start()
            except:
                break
    
    def _receive_from_client(self, conn, player_id):
        """从客户端接收数据 / Receive data from client"""
        while self.running:
            try:
                data = conn.recv(4096)
                if data:
                    with self.lock:
                        self.client_data[player_id] = pickle.loads(data)
            except:
                break
    
    def send_to_client(self, data, player_id=2):
        """发送数据给客户端 / Send data to client"""
        if len(self.connections) > 0:
            try:
                serialized = pickle.dumps(data)
                self.connections[0].sendall(serialized)
                return True
            except Exception as e:
                print(f"发送失败: {e} / Send failed: {e}")
                return False
        return False
    
    def get_client_data(self, player_id=2):
        """获取客户端数据 / Get client data"""
        with self.lock:
            data = self.client_data.get(player_id)
            if data:
                self.client_data[player_id] = None
            return data
    
    def has_client(self):
        """是否有客户端连接 / Check if client is connected"""
        return len(self.connections) > 0
    
    def close(self):
        """关闭服务器 / Close server"""
        self.running = False
        for conn in self.connections:
            try:
                conn.close()
            except:
                pass
        try:
            self.server.close()
        except:
            pass


def get_local_ip():
    """获取本机局域网IP / Get local LAN IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return socket.gethostbyname(socket.gethostname())