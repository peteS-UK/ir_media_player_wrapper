# IR Media Player Wrapper

WIP

A Home Assistant integration which wraps an IR only component in a media player entity.

## Installation

The preferred installation approach is via Home Assistant Community Store - aka [HACS](https://hacs.xyz/). The [repo](https://github.com/peteS-UK/ir_media_player_wrapper) is installable as a [Custom Repo](https://hacs.xyz/docs/faq/custom_repositories) via HACS.

If you want to download the integration manually, create a new folder called ir_media_player_wrapper under your custom_components folder in your config folder. If the custom_components folder doesn't exist, create it first. Once created, download the files and folders from the [github repo](https://github.com/peteS-UK/ir_media_player_wrapper/tree/main/custom_components/ir_media_player_wrapper) into this new folder.

Once downloaded either via HACS or manually, restart your Home Assistant server, and add the new integration.

## Configuration

The integration depends on you having captured the IR codes for your device using the remote.learn_command action. Here you need to specify a device name, which you use in the configuration of this component, and the names of each command. These names need to match the names of the features you select in the configuration e.g. Play, Pause, Turn On, Turn Off, etc.. For the Volume Up/Volume Down feature, you need to create two commands - Volume Up and Volume Down. The names are case sensitive.

## Options

You can update your list of sources and your selected featured by re-configuring the config option by clicking on the cog in the integration list.
