# Minecraft Whitelist Bot

A small self-hosted Discord bot that lets members with a specific role whitelist themselves on a Minecraft (Java) server via `/whitelist <username>`.

## Commands

- `/whitelist <username>` — usable only by members with the configured role.Validates the username against Mojang, then adds it via RCON.
- `/unwhitelist <username>` — admin-only (Discord "Administrator" permission), removes a username via RCON.

## Setup

### 1. Enable RCON on your Minecraft server

In `server.properties`:

```
enable-rcon=true
rcon.port=25575
rcon.password=CHOOSE_A_STRONG_PASSWORD
```

If you're using the `itzg/minecraft-server` Docker image, set the equivalent environment variables instead (`ENABLE_RCON: "true"`, `RCON_PASSWORD: "..."`, `RCON_PORT: "25575"`).

The bot needs to reach the RCON port, put it on the same Docker network as your Minecraft server and there's no need to publish the port anywhere else.

### 2. Create the Discord application

1. https://discord.com/developers/applications → **New Application**
2. **Bot** tab → **Reset Token** → this is your `DISCORD_TOKEN`. No
   privileged intents are required.
3. **OAuth2 → URL Generator** → scopes: `bot`, `applications.commands`.
   Bot permissions: **Send Messages**, **Use Slash Commands**.
4. Open the generated URL and invite the bot to your server.

### 3. Get your IDs

Enable Developer Mode (User Settings → Advanced → Developer Mode), then:
- Right-click your server icon → **Copy Server ID** → `GUILD_ID`
- Right-click the allowed role → **Copy Role ID** → `ALLOWED_ROLE_ID`

### 4. Configure 

Directly in Docker Compose
```yaml
  whitelist-bot:
    image: ghcr.io/Finalguardian01/mcDiscordWhitelister:latest
    container_name: whitelist-bot
    restart: unless-stopped
    environment:
      DISCORD_TOKEN: "your_bot_token"
      GUILD_ID: "your_guild_id"
      ALLOWED_ROLE_ID: "your_role_id"
      RCON_HOST: minecraft        # your MC server's container/service name
      RCON_PORT: "25575"
      RCON_PASSWORD: "your_rcon_password"
    networks:
      - <network_shared_with_your_mc_server>
```

Then:
```bash
docker compose up -d --build whitelist-bot
```

Or with plain `docker run`:
```bash
docker build -t mc-whitelist-bot .
docker run -d \
  --name whitelist-bot \
  -e DISCORD_TOKEN="your_bot_token" \
  -e GUILD_ID="your_guild_id" \
  -e ALLOWED_ROLE_ID="your_role_id" \
  -e RCON_HOST="minecraft" \
  -e RCON_PORT="25575" \
  -e RCON_PASSWORD="your_rcon_password" \
  --network <network_shared_with_your_mc_server> \
  --restart unless-stopped \
  ghcr.io/Finalguardian01/mcDiscordWhitelister:latest
```

### Alternative: running the bot on the host network

If your Minecraft server isn't in Docker (or isn't on the same Docker network as the bot), you can run the bot with `network_mode: host`. This makes the container share the host's network stack directly, so `RCON_HOST` can just be `127.0.0.1` (or `localhost`) if the Minecraft server is running on the same machine or the ip of another machine on your LAN if the server is running on it.

```yaml
  whitelist-bot:
  image: ghcr.io/Finalguardian01/mcDiscordWhitelister:latest
  container_name: whitelist-bot
    restart: unless-stopped
    network_mode: host
    environment:
      DISCORD_TOKEN: "your_bot_token"
      GUILD_ID: "your_guild_id"
      ALLOWED_ROLE_ID: "your_role_id"
      RCON_HOST: "127.0.0.1"
      RCON_PORT: "25575"
      RCON_PASSWORD: "your_rcon_password"
```

Then:
```bash
docker compose up -d --build whitelist-bot
```
Or with plain `docker run`:
```bash

docker run -d \
  --name whitelist-bot \
  --network host \
  -e DISCORD_TOKEN="your_bot_token" \
  -e GUILD_ID="your_guild_id" \
  -e ALLOWED_ROLE_ID="your_role_id" \
  -e RCON_HOST="127.0.0.1" \
  -e RCON_PORT="25575" \
  -e RCON_PASSWORD="your_rcon_password" \
  --restart unless-stopped \
  ghcr.io/Finalguardian01/mcDiscordWhitelister:latest
```


## Notes

- The bot never touches `whitelist.json` directly, everything goes through RCON, so no restart needed.
- **`network_mode: host` only works on Linux.** and is as of now only a beta function on Docker Desktop for Mac/Windows and may get silently ignored or be unsupported depending on version. You can use `host.docker.internal` as `RCON_HOST` there instead.

## License

MIT — see [LICENSE](LICENSE).
