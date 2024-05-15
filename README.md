# CTF Team Tool
Gday, this is a little bot I made for the CTF teams I play in [IrisSec](https://irissec.xyz/) and [thehackerscrew](https://www.thehackerscrew.team/) (one of them being quite disorganised with their channels previously) so I made this bot to automate the reaction role process, role creation, category, channels and the likes.

## .env Setup
Firstly, rename the `.env.template` to `.env`, here is a table for the key and value pairs that are expected.

| Key Name      | Value Type | Value Options | Optional? | Default Value | Purpose                                      |
|---------------|------------|---------------|-----------|---------------|----------------------------------------------|
| TOKEN         | String     | -             | No        | -             | The token for your Discord Bot               |
| GUILD_ID      | String     | -             | No        | -             | The ID for the Discord Server your bot is in |
| ADMIN_ROLE_ID | String     | -             | No        | -             | The role ID for the Administrator role       |

## Channel Customisation
The layout of channels is in the `channels.json` file. The array stores objects that contain both a `name` and a `channels` key, the `name` value being the name of the category and `channels` value being another array containing objects. The channels have a few keys listed below in this table.

| Key Name             | Value Type | Value Options    | Optional? | Default Value | Purpose                                                       |
|----------------------|------------|------------------|-----------|---------------|---------------------------------------------------------------|
| name                 | String     | -                | No        | -             | The name of the channel                                       |
| type                 | String     | text/voice/forum | No        | -             | The type of channel it creates                                |
| archive              | Bool       | true/false       | Yes       | false         | If the channel is archived when running the `archive` command |
| participant_editable | Bool       | true/false       | Yes       | true          | If the channel should be editable by participants             |

## To-do
- Have reaction role expiration on a timestamp so people cannot join mid-CTF (prevent potential cheating)
- CTF auto-archival at a timestamp
- Customisable emoji for a reaction message when creating a CTF

## Known Bugs
- When working with multiple categories we can hit some errors when archiving where channels do not go to the correct archival category when channels share the same name.
