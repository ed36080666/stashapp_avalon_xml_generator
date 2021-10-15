# Avalon XML Generator
[AvalonXMLAgent](https://github.com/joshuaavalon/AvalonXmlAgent.bundle) is an agent for Plex that populates metadata using local XML files.

This StashApp plugin hooks into the `Scene.Updated.Post` event and writes an XML file with the same name of the movie, in the same directory as the movie that can be consumed by the Avalon agent in Plex.

### Reminder
When installing this plugin into StashApp, you will need to customize the `LAN_ADDRESS` in the Python script to handle actor images. StashApp returns image URLs with `localhost` and these will not be accessible if you import the metadata into a different server on your network.

This value should be set to the LAN address of your StashApp server (only use localhost if everything is running on the same server).
