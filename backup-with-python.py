import paramiko
from scp import SCPClient
import os
from datetime import datetime

def create_ssh_client(hostname, username, password, port="***"):
    """
    Create an SSH client and connect to the host.
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, port, username, password)
    return ssh

def get_router_identity(ssh):
    """
    Retrieve the router's identity to use as the backup name.
    """
    command = "/system identity print"
    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode('utf-8')
    for line in output.splitlines():
        if "name:" in line:
            return line.split(":", 1)[1].strip()
    raise Exception("Could not retrieve router identity.")

def take_backup_rsc(ssh, backup_name):
    """
    Run the command on MikroTik to export the configuration in RSC format.
    """
    command = f"/export file={backup_name}"
    stdin, stdout, stderr = ssh.exec_command(command)
    stderr_output = stderr.read().decode('utf-8')
    if stderr_output:
        raise Exception(f"Error while taking RSC backup: {stderr_output}")

def download_backup(ssh, remote_path, local_path):
    """
    Download the backup file from MikroTik.
    """
    with SCPClient(ssh.get_transport()) as scp:
        scp.get(remote_path, local_path)

def main():
    # MikroTik connection details
    router_list = [
        {"hostname": "192.168.1.1", "username": "test", "password": "test"},
        # Add more routers here if needed
    ]

    for router in router_list:
        hostname = router["hostname"]
        username = router["username"]
        password = router["password"]

        try:
            # Connect to MikroTik
            ssh = create_ssh_client(hostname, username, password)

            # Retrieve router identity
            print(f"[{hostname}] Retrieving router identity...")
            router_identity = get_router_identity(ssh)
            timestamp = datetime.now().strftime("%Y-%m-%d")
            backup_name = f"{router_identity}_{timestamp}"
            print(f"[{hostname}] Router identity retrieved: {router_identity}")

            # Set backup paths
            remote_path = f"{backup_name}.rsc"  # Path on MikroTik
            local_path = os.path.join(os.getcwd(), remote_path)  # Path to save locally

            # Take backup in RSC format
            print(f"[{hostname}] Taking RSC backup...")
            take_backup_rsc(ssh, backup_name)
            print(f"[{hostname}] RSC backup created successfully.")

            # Download backup
            print(f"[{hostname}] Downloading backup...")
            download_backup(ssh, remote_path, local_path)
            print(f"[{hostname}] Backup downloaded successfully to {local_path}.")
        
        except Exception as e:
            print(f"[{hostname}] An error occurred: {e}")
        finally:
            if 'ssh' in locals():
                ssh.close()

if __name__ == "__main__":
    main()
