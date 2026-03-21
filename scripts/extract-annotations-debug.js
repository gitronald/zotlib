/**
 * Debug version - check attachments and annotations
 */

var output = [];
var zoteroPane = Zotero.getActiveZoteroPane();
var selectedItems = zoteroPane.getSelectedItems();
var item = selectedItems[0];
var parentItem = item.isAttachment() ? Zotero.Items.get(item.parentItemID) : item;
var attachmentIDs = parentItem.getAttachments();

output.push("Attachment IDs: " + JSON.stringify(attachmentIDs));

// Load attachments synchronously
var attachments = Zotero.Items.get(attachmentIDs);
output.push("Attachments loaded: " + attachments.length);

for (var i = 0; i < attachments.length; i++) {
    var att = attachments[i];
    output.push("  Attachment " + i + ":");
    output.push("    ID: " + att.id);
    output.push("    Content type: " + att.attachmentContentType);
    output.push("    Filename: " + att.attachmentFilename);

    // Check for annotations
    var annIDs = att.getAnnotations();
    output.push("    Annotation IDs: " + JSON.stringify(annIDs));

    if (annIDs.length > 0) {
        var annotations = Zotero.Items.get(annIDs);
        output.push("    Annotations loaded: " + annotations.length);
        for (var j = 0; j < Math.min(annotations.length, 3); j++) {
            var ann = annotations[j];
            output.push("      - Type: " + ann.annotationType);
            output.push("        Text: " + (ann.annotationText || "").substring(0, 80));
        }
    }
}

return output;
