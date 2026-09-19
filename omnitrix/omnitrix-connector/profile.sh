#!/usr/bin/env bash

# lyla_instance_launcher_profile declares the complete Omnitrix participant
# workflow. The generic launcher validates these values before it authenticates
# or contacts the Lyla instance APIs.
lyla_instance_launcher_profile() {
  local local_port=${LYLA_LOCAL_PORT:-"auto"}
  local forward

  # The launcher resolves this unexported value through lookup_key_source=auto.
  # shellcheck disable=SC2034
  LYLA_PROFILE_LOOKUP_KEY=${LYLA_PROFILE_LOOKUP_KEY:-cuq1HfFo}

  case "$local_port" in
    auto) forward=pwn-omnitrix:7878 ;;
    *) forward="${local_port}:pwn-omnitrix:7878" ;;
  esac

  lyla_instance_launcher_set display_name "Omnitrix"
  lyla_instance_launcher_set server "${LYLA_SERVER:-https://lyla.tisc26.ctf.sg}"
  lyla_instance_launcher_set provider "${LYLA_PROVIDER:-ctf.sg}"
  lyla_instance_launcher_set flow password
  lyla_instance_launcher_set username_env LYLA_USERNAME
  lyla_instance_launcher_set profile urn:ttyusb-dev:lyla:v1:profile:pwn-omnitrix
  lyla_instance_launcher_set lookup_key_source auto
  lyla_instance_launcher_set create_key_source none
  lyla_instance_launcher_set max_connections 128
  lyla_instance_launcher_add_forward "$forward"
}
