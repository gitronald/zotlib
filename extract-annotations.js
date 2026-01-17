/**
 * Zotero 7 Script: Extract Annotations to Markdown
 *
 * Usage: Select an item in Zotero, then run this script in
 * Tools > Developer > Run JavaScript
 */

var zoteroPane = Zotero.getActiveZoteroPane();
var selectedItems = zoteroPane.getSelectedItems();

if (selectedItems.length === 0) {
    "ERROR: Please select an item first.";
} else if (selectedItems.length > 1) {
    "ERROR: Please select only one item.";
} else {
    (function() {
        var item = selectedItems[0];
        var parentItem = item.isAttachment() ? Zotero.Items.get(item.parentItemID) : item;

        if (!parentItem) {
            return "ERROR: Could not find parent item.";
        }

        // Get PDF attachments
        var attachmentIDs = parentItem.getAttachments();
        var attachments = Zotero.Items.get(attachmentIDs);
        var pdfAttachments = attachments.filter(function(att) {
            return att.attachmentContentType === 'application/pdf';
        });

        if (pdfAttachments.length === 0) {
            return "ERROR: No PDF attachments found.";
        }

        // Collect all annotations from all PDFs
        var allAnnotations = [];
        for (var i = 0; i < pdfAttachments.length; i++) {
            var annData = pdfAttachments[i].getAnnotations();
            // getAnnotations() returns annotation objects directly
            for (var j = 0; j < annData.length; j++) {
                var ann = annData[j];
                // Handle both object and JSON string formats
                if (typeof ann === 'string') {
                    ann = JSON.parse(ann);
                }
                allAnnotations.push(ann);
            }
        }

        if (allAnnotations.length === 0) {
            return "ERROR: No annotations found in the PDF.";
        }

        // Sort by page then position
        allAnnotations.sort(function(a, b) {
            var posA = typeof a.annotationPosition === 'string' ? JSON.parse(a.annotationPosition) : (a.annotationPosition || {});
            var posB = typeof b.annotationPosition === 'string' ? JSON.parse(b.annotationPosition) : (b.annotationPosition || {});
            var pageA = posA.pageIndex || 0;
            var pageB = posB.pageIndex || 0;
            if (pageA !== pageB) return pageA - pageB;
            // Use sortIndex if available
            var sortA = a.annotationSortIndex || '';
            var sortB = b.annotationSortIndex || '';
            return sortA.localeCompare(sortB);
        });

        // Build markdown
        var markdown = [];
        var title = parentItem.getField('title') || 'Untitled';
        var creators = parentItem.getCreators();
        var authors = creators
            .filter(function(c) { return c.creatorType === 'author'; })
            .map(function(c) { return c.lastName ? (c.lastName + ', ' + (c.firstName || '')).trim() : c.name; })
            .join('; ');
        var year = parentItem.getField('year') || (parentItem.getField('date') || '').substring(0, 4);

        markdown.push('# Annotations: ' + title);
        markdown.push('');
        if (authors) markdown.push('**Authors:** ' + authors);
        if (year) markdown.push('**Year:** ' + year);
        markdown.push('**Extracted:** ' + new Date().toLocaleDateString());
        markdown.push('**Total Annotations:** ' + allAnnotations.length);
        markdown.push('');
        markdown.push('---');
        markdown.push('');

        // Process annotations
        var currentPage = -1;

        function getColorLabel(color) {
            if (!color) return '';
            var hex = color.toLowerCase();
            if (hex === '#ffd400' || hex === '#ffff00') return '[yellow]';
            if (hex === '#ff6666' || hex === '#ff0000') return '[red]';
            if (hex === '#5fb236' || hex === '#00ff00') return '[green]';
            if (hex === '#2ea8e5' || hex === '#0000ff') return '[blue]';
            if (hex === '#a28ae5' || hex === '#800080') return '[purple]';
            if (hex === '#e56eee') return '[magenta]';
            if (hex === '#f19837') return '[orange]';
            return '[' + color + ']';
        }

        for (var k = 0; k < allAnnotations.length; k++) {
            var ann = allAnnotations[k];
            var type = ann.annotationType || '';
            var text = ann.annotationText || '';
            var comment = ann.annotationComment || '';
            var color = ann.annotationColor || '';
            var position = typeof ann.annotationPosition === 'string' ? JSON.parse(ann.annotationPosition) : (ann.annotationPosition || {});
            var page = (position.pageIndex || 0) + 1;

            // Page header
            if (page !== currentPage) {
                currentPage = page;
                markdown.push('## Page ' + page);
                markdown.push('');
            }

            // Format by type
            if (type === 'highlight') {
                var colorLabel = getColorLabel(color);
                markdown.push(colorLabel + ' **Highlight:**');
                markdown.push('> ' + text.replace(/\n/g, '\n> '));
                if (comment) {
                    markdown.push('');
                    markdown.push('**Note:** ' + comment);
                }
                markdown.push('');
            } else if (type === 'note') {
                markdown.push('**Note:**');
                markdown.push(comment || text);
                markdown.push('');
            } else if (type === 'underline') {
                markdown.push('**Underline:**');
                markdown.push('> ' + text.replace(/\n/g, '\n> '));
                if (comment) {
                    markdown.push('');
                    markdown.push('**Note:** ' + comment);
                }
                markdown.push('');
            } else if (type === 'image') {
                markdown.push('**Image annotation:**');
                if (comment) markdown.push(comment);
                markdown.push('*(Image not exported)*');
                markdown.push('');
            } else {
                markdown.push('**' + type + ':**');
                if (text) markdown.push('> ' + text.replace(/\n/g, '\n> '));
                if (comment) markdown.push('**Note:** ' + comment);
                markdown.push('');
            }
        }

        var markdownContent = markdown.join('\n');

        // Save file
        var fp = new FilePicker();
        fp.init(window, "Save Annotations as Markdown", fp.modeSave);
        fp.appendFilters(fp.filterAll);
        var safeTitle = title.replace(/[<>:"/\\|?*]/g, '_');
        fp.defaultString = safeTitle + '_annotations.md';

        fp.show().then(function(result) {
            if (result === fp.returnOK || result === fp.returnReplace) {
                var outputPath = fp.file;
                if (!outputPath.endsWith('.md')) {
                    outputPath += '.md';
                }
                Zotero.File.putContentsAsync(outputPath, markdownContent).then(function() {
                    alert('Annotations saved to:\n' + outputPath);
                });
            }
        });

        return "Processing " + allAnnotations.length + " annotations...";
    })();
}
