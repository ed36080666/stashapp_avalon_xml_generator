# Avalon XML Generator
[AvalonXMLAgent](https://github.com/joshuaavalon/AvalonXmlAgent.bundle) is an agent for Plex that populates metadata using local XML files.

This StashApp plugin hooks into the `Scene.Updated.Post` event and writes an XML file with the same name of the movie, in the same directory as the movie that can be consumed by the Avalon agent in Plex.
