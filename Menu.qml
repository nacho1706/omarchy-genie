import QtQuick

// Declare the app grid as a menu so Omarchy grants its application-library
// capability. The persistent service still owns the single dock and app grid.
Item {
    property var shell: null
    property var manifest: null
    property var service: null
    readonly property bool opened: service ? service.appsOpened : false

    function open() { if (service) service.openApps() }
    function close() { if (service) service.closeApps() }
    function toggle() { if (opened) close(); else open() }
}
