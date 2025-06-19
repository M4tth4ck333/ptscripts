Egress Port Scanner
    
   A multi-threaded egress port scanner designed to test outbound connectivity by querying a specific HTTP endpoint on configurable ports. Supports:
    
        Customizable port ranges and multi-threading
    
        Timeout and retry logic per port
    
        Optional logging of scan results to SQLite or PostgreSQL databases
    
        Verbose mode for detailed output
    
   Features
    
        Scan single ports, comma-separated ports, or port ranges (e.g., 80, 20-25, 80,443,8000-8010)
    
        Control concurrency via configurable thread count
    
        Specify socket timeout and retry attempts to improve reliability
    
        Persist scan results in SQLite3 or PostgreSQL for later analysis
    
        Clean, thread-safe design using Python 3 standard libraries and psycopg2 for PostgreSQL
    
  Installation
  Clone the repository:
    
    git clone https://github.com/yourusername/egress-port-scanner.git
    cd egress-port-scanner
    Install dependencies (PostgreSQL support)
    Usage
      
      python3 egress_scan.py -p <ports> [options]
      
      Required arguments:
      
          -p, --ports
          Specify port(s) to scan. Supports single port, comma-separated list, and ranges.
          Examples:
          80
          80,443,8080
          20-25
          22,80-90
      
      Optional arguments:
      
          -t, --threads
          Number of concurrent threads (default: 5)
      
          --timeout
          Socket timeout in seconds (default: 3)
      
          --retries
          Number of retries per port on failure (default: 3)
      
          -v, --verbose
          Enable verbose output, showing allowed ports
      
          --sqlite
          Path to SQLite DB file to save scan results (optional)
      
          --pg
          PostgreSQL DSN connection string (optional), e.g.
          "dbname=test user=postgres password=secret"
      
      Examples
      
      Scan ports 80, 443, and 8000-8010 with 10 threads and verbose output:
      
      python3 egress_scan.py -p 80,443,8000-8010 -t 10 -v
      
      Scan ports 22-30, saving results in SQLite:
      
      python3 egress_scan.py -p 22-30 --sqlite ./scan_results.db -v
      
      Scan ports 80 and 443, saving results to PostgreSQL:
      
      python3 egress_scan.py -p 80,443 --pg "dbname=mydb user=postgres password=secret" -v

  Dependencies

    Python 3.6+

    psycopg2-binary (if using PostgreSQL support)
    
    License
    
    MIT License — feel free to use and modify.
