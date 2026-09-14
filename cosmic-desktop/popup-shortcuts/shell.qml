import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io

ShellRoot {
    id: root

    property var shortcuts: []

    function matches(item) {
        const q = search.text.toLowerCase().trim()

        return q === ""
            || item.shortcut.toLowerCase().includes(q)
            || item.description.toLowerCase().includes(q)
            || item.category.toLowerCase().includes(q)
    }

    function matchingCount() {
        return root.shortcuts.filter(function(item) {
            return root.matches(item)
        }).length
    }

    Process {
        id: shortcutLoader
        command: [
            "/usr/bin/python3",
            "/home/bart/.config/quickshell-shortcuts/shortcuts.py"
        ]

        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    root.shortcuts = JSON.parse(this.text)
                } catch (e) {
                    console.log("JSON ERROR:", e)
                }
            }
        }
    }

    Component.onCompleted: {
        shortcutLoader.running = true
    }

    PanelWindow {
        id: panel

        anchors {
            top: true
            bottom: true
            left: true
            right: true
        }

        color: "#66000000"
        exclusiveZone: 0
        focusable: true

        Shortcut {
            sequence: "Escape"
            onActivated: Qt.quit()
        }

        Rectangle {
            id: popup

            width: 900
            height: 650
            anchors.centerIn: parent
            radius: 22
            color: "#ee151515"
            border.width: 1
            border.color: "#383838"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 28
                spacing: 18

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    Rectangle {
                        width: 42
                        height: 42
                        radius: 11
                        color: "#292929"

                        Text {
                            anchors.centerIn: parent
                            text: "⌨"
                            color: "#eeeeee"
                            font.pixelSize: 21
                        }
                    }

                    ColumnLayout {
                        spacing: 1

                        Text {
                            text: "Keyboard Shortcuts"
                            color: "#f5f5f5"
                            font.pixelSize: 24
                            font.weight: Font.DemiBold
                        }

                        Text {
                            text: "COSMIC Desktop"
                            color: "#888888"
                            font.pixelSize: 13
                        }
                    }

                    Item {
                        Layout.fillWidth: true
                    }

                    Rectangle {
                        width: 54
                        height: 30
                        radius: 8
                        color: "#242424"
                        border.width: 1
                        border.color: "#3b3b3b"

                        Text {
                            anchors.centerIn: parent
                            text: "ESC"
                            color: "#999999"
                            font.pixelSize: 11
                            font.weight: Font.Medium
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 54
                    radius: 14
                    color: "#202020"
                    border.width: search.activeFocus ? 1 : 0
                    border.color: "#777777"

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 17
                        anchors.rightMargin: 17
                        spacing: 12

                        Text {
                            text: "⌕"
                            color: "#999999"
                            font.pixelSize: 25
                        }

                        TextField {
                            id: search
                            Layout.fillWidth: true
                            focus: true
                            placeholderText: "Search shortcuts..."
                            placeholderTextColor: "#777777"
                            color: "#eeeeee"
                            font.pixelSize: 16
                            background: Item {}
                            Keys.onEscapePressed: Qt.quit()
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true

                    Text {
                        text: search.text.length > 0
                            ? "SEARCH RESULTS"
                            : "ALL SHORTCUTS"
                        color: "#777777"
                        font.pixelSize: 11
                        font.weight: Font.Bold
                        font.letterSpacing: 1.2
                    }

                    Item {
                        Layout.fillWidth: true
                    }

                    Text {
                        text: root.matchingCount() + " shortcuts"
                        color: "#666666"
                        font.pixelSize: 12
                    }
                }

                Flickable {
                    id: scroller
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    contentWidth: width
                    contentHeight: listColumn.implicitHeight

                    ScrollBar.vertical: ScrollBar {
                        policy: ScrollBar.AsNeeded
                    }

                    Column {
                        id: listColumn
                        width: scroller.width
                        spacing: 3

                        Repeater {
                            model: root.shortcuts

                            delegate: Column {
                                required property var modelData
                                required property int index

                                property bool itemMatches: root.matches(modelData)

                                property bool showCategory: {
                                    if (!itemMatches)
                                        return false

                                    for (let i = index - 1; i >= 0; i--) {
                                        if (root.matches(root.shortcuts[i])) {
                                            return root.shortcuts[i].category
                                                !== modelData.category
                                        }
                                    }

                                    return true
                                }

                                width: listColumn.width
                                visible: itemMatches
                                spacing: 4

                                Text {
                                    visible: showCategory
                                    text: modelData.category.toUpperCase()
                                    color: "#8a8a8a"
                                    font.pixelSize: 11
                                    font.weight: Font.Bold
                                    font.letterSpacing: 1.2
                                    leftPadding: 10
                                    topPadding: 14
                                    bottomPadding: 6
                                }

                                Rectangle {
                                    width: listColumn.width
                                    height: 50
                                    radius: 10
                                    color: mouseArea.containsMouse
                                        ? "#242424"
                                        : "transparent"

                                    Behavior on color {
                                        ColorAnimation {
                                            duration: 80
                                        }
                                    }

                                    MouseArea {
                                        id: mouseArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                    }

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.leftMargin: 12
                                        anchors.rightMargin: 12
                                        spacing: 16

                                        Row {
                                            Layout.preferredWidth: 355
                                            spacing: 6

                                            Repeater {
                                                model: modelData.shortcut.split(" + ")

                                                delegate: Rectangle {
                                                    required property string modelData
                                                    width: keyText.implicitWidth + 18
                                                    height: 30
                                                    radius: 7
                                                    color: "#292929"
                                                    border.width: 1
                                                    border.color: "#414141"

                                                    Text {
                                                        id: keyText
                                                        anchors.centerIn: parent
                                                        text: modelData.toUpperCase()
                                                        color: "#d8d8d8"
                                                        font.pixelSize: 11
                                                        font.weight: Font.DemiBold
                                                    }
                                                }
                                            }
                                        }

                                        Text {
                                            Layout.fillWidth: true
                                            text: modelData.description
                                            color: "#dedede"
                                            font.pixelSize: 15
                                            elide: Text.ElideRight
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    color: "#303030"
                }

                RowLayout {
                    Layout.fillWidth: true

                    Text {
                        text: "Type to filter"
                        color: "#666666"
                        font.pixelSize: 11
                    }

                    Item {
                        Layout.fillWidth: true
                    }

                    Text {
                        text: "COSMIC shortcuts"
                        color: "#555555"
                        font.pixelSize: 11
                    }
                }
            }
        }
    }
}
