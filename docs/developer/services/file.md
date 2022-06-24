# File Service

In the `lume-services` package

## Location encoding

Files locations are described and identified using Internate Assigned Numbers Authority [file URI scheme](https://www.rfc-editor.org/rfc/rfc8089.html). The FileService object is responsible for handling IO

Authority
explicit authority: file://ard@host.example.com/path/to/file"

empty authority:
file:///sdf-ard/path/to/file




local

  o  A traditional file URI for a local file with an empty authority.
      For example:

      *  "file:///path/to/file"

   o  The minimal representation of a local file with no authority field
      and an absolute path that begins with a slash "/".  For example:

      *  "file:/path/to/file"
