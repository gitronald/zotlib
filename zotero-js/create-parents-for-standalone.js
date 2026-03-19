/**
 * Zotero Script: Create parent items for standalone PDF attachments
 *
 * Finds standalone PDF attachments in a collection and creates a parent
 * document item for each, using the PDF filename (minus extension) as
 * the title. The attachment is then re-parented under the new item.
 *
 * Usage: Run via Tools > Developer > Run JavaScript, or via the debug
 * endpoint with run-create-parents.sh
 */

var COLLECTION_NAME = 'reviews';
var output = [];

// reviews collection (id=7, subcollection of writing)
var collection = Zotero.Collections.get(7);

if (!collection) {
    output.push("");
    output.push("ERROR: Collection '" + COLLECTION_NAME + "' not found in any library.");
    return output;
}

output.push("");
output.push("Found collection '" + COLLECTION_NAME + "' in library " + collection.libraryID);

var itemIDs = collection.getChildItems(true);
var items = Zotero.Items.get(itemIDs);
output.push("Items in collection: " + items.length);

var standalone = items.filter(function(item) {
    return item.isAttachment()
        && !item.parentItemID
        && item.attachmentContentType === 'application/pdf';
});
output.push("Standalone PDFs found: " + standalone.length);

function cleanTitle(rawPath) {
    // Strip "attachments:" or "storage:" prefix, then get filename without extension
    var clean = rawPath.replace(/^(attachments|storage):/, '');
    var filename = clean.split('/').pop().split('\\').pop();
    return filename.replace(/\.pdf$/i, '').replace(/_/g, ' ') || null;
}

for (var i = 0; i < standalone.length; i++) {
    var att = standalone[i];
    var path = att.attachmentPath || att.attachmentFilename || '';
    var title = cleanTitle(path) || ('Untitled attachment ' + att.id);

    // Create parent item
    var parent = new Zotero.Item('document');
    parent.libraryID = att.libraryID;
    parent.setField('title', title);
    await parent.saveTx();

    // Add parent to the same collection
    collection.addItem(parent.id);
    await collection.saveTx();

    // Re-parent the attachment under the new item
    att.parentItemID = parent.id;
    await att.saveTx();

    // Remove the now-child attachment from the collection
    collection.removeItem(att.id);
    await collection.saveTx();

    output.push("  [" + (i+1) + "/" + standalone.length + "] Created parent: " + title);
}

output.push("");
output.push("Done. Created " + standalone.length + " parent items.");

return output;
