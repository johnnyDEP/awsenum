import requests
import argparse
from rich.console import Console
from rich.table import Table
from rich import box
import json

def probe_artifactory_endpoints(artifactory_url, username, jwt):
    """
    Dynamically probe Artifactory API endpoints and display sample data in rich text tables
    
    Args:
        artifactory_url (str): Base URL of the Artifactory instance
        username (str): Artifactory username
        jwt (str): JWT token for authentication
    """
    # Set up headers with JWT authentication
    headers = {
        "Authorization": f"Bearer {jwt}",
        "Content-Type": "application/json"
    }
    
    # Define common Artifactory API endpoints (based on JFrog REST API docs)
    endpoints = {
        "System Version": {"path": "/api/system/version", "method": "GET"},
        "Repositories": {"path": "/api/repositories", "method": "GET"},
        "Storage Summary": {"path": "/api/storageinfo", "method": "GET"},
        "Users": {"path": "/api/security/users", "method": "GET"},  # Requires admin
        "Groups": {"path": "/api/security/groups", "method": "GET"},  # Requires admin
        "Permissions": {"path": "/api/security/permissions", "method": "GET"},  # Requires admin
        "Builds": {"path": "/api/build", "method": "GET"},
        "AQL Search (Sample)": {
            "path": "/api/search/aql",
            "method": "POST",
            "data": 'items.find({"type":"file"}).limit(2).include("name","repo","path")'
        }
    }
    
    # Initialize rich console
    console = Console()
    
    for endpoint_name, config in endpoints.items():
        try:
            url = f"{artifactory_url}{config['path']}"
            method = config.get("method", "GET")
            data = config.get("data", None)
            
            # Make the API request
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                headers["Content-Type"] = "text/plain"  # AQL uses plain text
                response = requests.post(url, headers=headers, data=data, timeout=10)
            
            # Check if request was successful
            response.raise_for_status()
            
            # Parse JSON response
            result = response.json()
            
            # Create a table for this endpoint
            table = Table(
                title=f"Endpoint: {endpoint_name} ({config['path']})",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold magenta",
                title_style="bold cyan"
            )
            
            # Handle different response structures
            if isinstance(result, dict):
                table.add_column("Key", style="cyan", no_wrap=True)
                table.add_column("Value", style="green")
                for key, value in result.items():
                    # Truncate long values for display
                    value_str = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                    table.add_row(key, value_str)
            elif isinstance(result, list) and result:
                # For lists, use the first item as a sample
                sample = result[0]
                table.add_column("Key", style="cyan", no_wrap=True)
                table.add_column("Value", style="green")
                for key, value in sample.items():
                    value_str = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                    table.add_row(key, value_str)
                table.add_row("Total Items", str(len(result)))
            else:
                table.add_column("Result", style="green")
                table.add_row(str(result))
            
            # Print the table
            console.print(table)
            console.print("")  # Add spacing between tables
            
        except requests.exceptions.RequestException as e:
            console.print(f"[red]Error probing {endpoint_name} ({config['path']}): {str(e)}[/red]")
            console.print("")
        except ValueError as e:
            console.print(f"[red]Error parsing response for {endpoint_name} ({config['path']}): {str(e)}[/red]")
            console.print("")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Probe all Artifactory API endpoints and display sample data")
    parser.add_argument("--url", required=True, help="Artifactory instance URL (e.g., https://your-artifactory.jfrog.io/artifactory)")
    parser.add_argument("--username", required=True, help="Artifactory username")
    parser.add_argument("--jwt", required=True, help="JWT token for authentication")
    
    # Parse arguments
    args = parser.parse_args()
    
    print("Probing Artifactory API endpoints...")
    probe_artifactory_endpoints(args.url, args.username, args.jwt)

if __name__ == "__main__":
    # Install required packages:
    # pip install requests rich
    main()
