@echo off
REM Starts the Retail Suite Docker test bench after a machine/Docker Desktop
REM restart. The containers auto-restart on their own (restart policy is set
REM to "unless-stopped"), but bench serve inside retail-bench does not - it
REM runs as a plain background command, not the container's own init
REM process, so it needs to be launched again each time.

echo Waiting for Docker Desktop...
:waitloop
docker info >nul 2>&1
if errorlevel 1 (
    timeout /t 3 >nul
    goto waitloop
)

echo Starting containers...
docker start retail-mariadb retail-redis-cache retail-redis-queue retail-bench

echo Waiting for MariaDB...
timeout /t 8 >nul

echo Re-linking node in retail-bench...
docker exec -u root retail-bench bash -c "for f in /home/frappe/.nvm/versions/node/v20.19.2/bin/*; do ln -sf $f /usr/local/bin/$(basename $f); done"

echo Starting bench serve...
docker exec -d retail-bench bash -lc "cd /home/frappe/frappe-bench && bench serve --port 8000 > /home/frappe/frappe-bench/logs/bench-serve.log 2>&1"

timeout /t 6 >nul
echo Done. Site should be available at http://localhost:8321
pause
