# Challenge access package

This package starts or resumes a challenge instance and opens an authenticated
TCP forward from the local computer to the challenge service. The packaged
profile supplies the server, identity provider, challenge identifier, access
key, and forwarding targets.

## Supported environments

The included client is built for Linux on amd64 (`linux/amd64`) only.

- amd64 Linux runs the package directly.
- Windows runs the package inside an amd64 WSL2 Linux distribution.
- macOS runs the package inside a Docker container using the `linux/amd64`
  platform. On Apple silicon, Docker Desktop uses Rosetta for amd64 emulation.

Native Windows and macOS execution is not supported. Run `uname -m` in the Linux
environment and confirm that it prints `x86_64` before using the direct Linux
instructions.

## Package contents

| File | Purpose |
|------|---------|
| `launcher.sh` | Authenticates, creates or resumes the instance, monitors startup, and manages local access |
| `lyla-client` | Linux/amd64 client used by the launcher |
| `profile.sh` | Server, provider, challenge, access-key, and forwarding declaration |

Keep these files in the same directory. The launcher discovers the adjacent
`lyla-client` and `profile.sh` automatically, regardless of the current directory.

## Linux

Open a terminal in the extracted package directory:

```bash
chmod +x launcher.sh lyla-client
./launcher.sh
```

The launcher prompts for the configured provider's credentials when it cannot
reuse a stored session. It prints each selected local address after the
challenge workload becomes ready. A profile with several forwarding targets
produces one entry per target:

```text
Local connection
  127.0.0.1:35251 → challenge:7878

Local connection
  127.0.0.1:35252 → web:8080
```

Connect each challenge tool to its corresponding local address. For example:

```bash
nc 127.0.0.1 35251
```

The service names, remote ports, and number of forwards come from `profile.sh`.
Automatically selected local ports can differ on each invocation.

## Windows with WSL2

Copy or extract the package inside the WSL2 Linux filesystem, then run it from a
WSL2 terminal:

```bash
cd ~/challenge-access
chmod +x launcher.sh lyla-client
./launcher.sh
```

Use the local address printed by the launcher. WSL2 forwards its localhost ports
to the Windows host under the standard WSL2 networking configuration. A client
can also connect from inside the WSL2 distribution.

Do not run `launcher.sh` or `lyla-client` from PowerShell or Command Prompt; both
artifacts require Linux.

## macOS with Docker

On Apple silicon, select the Apple Virtualization framework and enable
**Use Rosetta for x86_64/amd64 emulation** in
[Docker Desktop settings](https://docs.docker.com/desktop/settings-and-maintenance/settings/).

Run this command from the package directory:

```bash
docker run --rm -it \
  --platform linux/amd64 \
  -p 127.0.0.1:7878:7878 \
  -e LYLA_LOCAL_PORT=7878 \
  -v "$PWD:/opt/challenge:ro" \
  -w /opt/challenge \
  debian:bookworm-slim \
  sh -c 'apt-get update &&
    apt-get install -y --no-install-recommends bash ca-certificates coreutils gawk gzip tar &&
    rm -rf /var/lib/apt/lists/* &&
    exec ./launcher.sh -- --address 0.0.0.0'
```

Connect to `127.0.0.1:7878` on macOS while the launcher is running. The Docker
publish rule exposes the container listener only on the host's loopback address.
If that port is unavailable, change `7878` consistently in the publish rule and
`LYLA_LOCAL_PORT` value.

## Launcher behavior

The launcher:

- signs in when needed;
- creates or resumes the challenge instance;
- shows startup progress and the challenge expiry time; and
- keeps local connections open until the command exits or the instance expires.

Press `Ctrl-C` to stop local access. This does not immediately delete the remote
instance; rerunning the launcher resumes an eligible instance until it expires.

Pass `--recreate` to replace the selected instance before starting:

```bash
./launcher.sh --recreate
```

Set a fixed local port on Linux or WSL2 when required:

```bash
LYLA_LOCAL_PORT=7878 ./launcher.sh
```

## Troubleshooting

### The client cannot execute

An `Exec format error` or `cannot execute binary file` message usually means the
Linux environment is not amd64. Confirm that `uname -m` prints `x86_64`, or use
the Docker command with `--platform linux/amd64`.

### The launcher cannot find the client

Confirm that `launcher.sh` and `lyla-client` are in the same directory and that
the client is executable:

```bash
chmod +x launcher.sh lyla-client
./launcher.sh --check
```

### A selected local port is occupied

On Linux or WSL2, let the profile select available loopback ports or configure
different fixed ports. For Docker, every fixed container port needs a matching
loopback-only publish rule.

### The instance expired

Run `./launcher.sh` again. The launcher waits for bounded cleanup of the expired
record before requesting a replacement instance.
