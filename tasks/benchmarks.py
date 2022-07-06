from invoke import task

from . import run


@task
def benchmark_wrk_docker(c):
    c.run(
        "docker run -it --rm --network host"
        " -v $(pwd):/root"
        " tullo/wrk2"
        " --threads=1"
        " --connections=10"
        " --duration=10s"
        " --rate=10"
        " --latency"
        f" http://localhost:{run.PORT}"
    )


@task
def benchmark_httperf(c):
    c.run(f"httperf --server=localhost --port={run.PORT} --uri=/ --wsess=10,10,0 --burst-len=2")


@task
def benchmark_ab_docker(c):
    result = c.run(
        "docker network inspect bridge --format='{{ range .IPAM.Config }}{{ println .Gateway }}{{ end }}' | xargs",
        hide=True,
    )
    host = f"http://{result.stdout.strip()}:{run.PORT}"
    # k=keepalive, c=concurrency, t=timelimit(implies -n 50000), n=requests(count)
    c.run(f"docker run --rm jordi/ab -k -c10 -t5 {host}/")
