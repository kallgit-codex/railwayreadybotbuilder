"""
Client Service - Handles client management operations
"""
import json
from typing import Dict, List, Optional


class ClientService:
    """Service for managing clients and their configurations"""
    
    @staticmethod
    def create_client(name: str, notes: str = "", api_keys: Dict = None) -> Dict:
        """Create a new client with optional API keys"""
        try:
            # Import here to avoid circular imports
            from models import Client, db
            
            # Create new client
            client = Client(
                name=name,
                notes=notes,
                api_keys=json.dumps(api_keys or {})
            )
            
            db.session.add(client)
            db.session.commit()
            
            return {
                'success': True,
                'client': client.to_dict(),
                'message': 'Client created successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to create client'
            }
    
    @staticmethod
    def get_all_clients() -> List[Dict]:
        """Get all clients with their bot counts"""
        try:
            # Import here to avoid circular imports
            from models import Client
            clients = Client.query.order_by(Client.created_at.desc()).all()
            return [client.to_dict() for client in clients]
        except Exception as e:
            print(f"Error fetching clients: {e}")
            return []
    
    @staticmethod
    def get_client_by_id(client_id: int) -> Optional[Dict]:
        """Get a specific client with their bots"""
        try:
            # Import here to avoid circular imports
            from models import Client
            client = Client.query.get(client_id)
            if not client:
                return None
            
            client_data = client.to_dict()
            client_data['bots'] = [bot.to_dict() for bot in client.bots]
            
            return client_data
        except Exception as e:
            print(f"Error fetching client {client_id}: {e}")
            return None
    
    @staticmethod
    def update_client(client_id: int, name: str = None, notes: str = None, api_keys: Dict = None) -> Dict:
        """Update client information and API keys"""
        try:
            # Import here to avoid circular imports
            from models import Client, db
            client = Client.query.get(client_id)
            if not client:
                return {
                    'success': False,
                    'error': 'Client not found',
                    'message': 'Client does not exist'
                }
            
            # Update fields if provided
            if name is not None:
                client.name = name
            if notes is not None:
                client.notes = notes
            if api_keys is not None:
                client.api_keys = json.dumps(api_keys)
            
            db.session.commit()
            
            return {
                'success': True,
                'client': client.to_dict(),
                'message': 'Client updated successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to update client'
            }
    
    @staticmethod
    def delete_client(client_id: int) -> Dict:
        """Delete a client and all associated bots"""
        try:
            client = Client.query.get(client_id)
            if not client:
                return {
                    'success': False,
                    'error': 'Client not found',
                    'message': 'Client does not exist'
                }
            
            # Store client name for response
            client_name = client.name
            bot_count = len(client.bots)
            
            # Delete client (cascade will delete associated bots)
            db.session.delete(client)
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Client "{client_name}" and {bot_count} associated bots deleted successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to delete client'
            }
    
    @staticmethod
    def get_client_api_keys(client_id: int) -> Dict:
        """Get API keys for a specific client"""
        try:
            client = Client.query.get(client_id)
            if not client:
                return {}
            
            return json.loads(client.api_keys) if client.api_keys else {}
        except Exception as e:
            print(f"Error fetching API keys for client {client_id}: {e}")
            return {}
    
    @staticmethod
    def update_api_keys(client_id: int, api_keys: Dict) -> Dict:
        """Update API keys for a specific client"""
        try:
            client = Client.query.get(client_id)
            if not client:
                return {
                    'success': False,
                    'error': 'Client not found',
                    'message': 'Client does not exist'
                }
            
            client.api_keys = json.dumps(api_keys)
            db.session.commit()
            
            return {
                'success': True,
                'api_keys': api_keys,
                'message': 'API keys updated successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to update API keys'
            }