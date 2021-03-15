/*
 * Fedora Media Writer
 * Copyright (C) 2016 Martin Bříza <mbriza@redhat.com>
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
 */

import QtQuick 2.15
import QtQuick.Controls 2.12 as QQC2
import QtQuick.Layouts 1.12
//import MediaWriter 1.0

import "../simple"

Item {
    id: root
    width: parent.width
    height: Math.round(_units.grid_unit * 4.5)
    activeFocusOnTab: true

    readonly property bool isTop: false
    readonly property bool isBottom: true
    //readonly property bool isTop: !_releases.get(index-1) || (_release.category !== _releases.get(index-1).category)
    //readonly property bool isBottom:
//        typeof _release !== 'undefined' &&
//        !_releases.front_page &&
//        (!_releases.get(index+1) ||
//         typeof _releases.get(index+1) == 'undefined' ||
//         (_release && _release.category !== _releases.get(index+1).category)
//        )

    property color color: delegateMouse.containsPress ? Qt.darker(palette.button, 1.2) : delegateMouse.containsMouse ? palette.button : palette.background
    Behavior on color { ColorAnimation { duration: 120 } }

    readonly property real animationDuration: 1000

    Rectangle {
        width: parent.width - 2
        height: parent.height + 1
        x: 1
        color: root.color
        border {
            color: Qt.darker(palette.window, 1.2)
            width: 1
        }
        Item {
            id: iconRect
            anchors {
                top: parent.top
                left: parent.left
                bottom: parent.bottom
                leftMargin: _units.grid_unit * 2
                topMargin: _units.grid_unit
                bottomMargin: anchors.topMargin
            }
            width: height
            IndicatedImage {
                fillMode: Image.PreserveAspectFit
                source: _release.icon
                sourceSize.height: parent.height
                sourceSize.width: parent.width
            }
        }
        ColumnLayout {
            id: textRect
            spacing: _units.small_spacing
            anchors {
                verticalCenter: parent.verticalCenter
                left: iconRect.right
                right: arrow.left
                leftMargin: _units.grid_unit * 2
                rightMargin: _units.grid_unit * 2
            }
            RowLayout {
                spacing: 0
                QQC2.Label {
                    verticalAlignment: Text.AlignBottom
                    text: model.class_descr
                }
                QQC2.Label {
                    text: " " + model.name
                    //visible: !release.isLocal
                    visible: true
                }
            }
            QQC2.Label {
                Layout.fillWidth: true
                verticalAlignment: Text.AlignTop
                text: model.key
                wrapMode: Text.Wrap
                opacity: 0.6
            }
        }
        Arrow {
            id: arrow
            //visible: !release.isLocal
            visible: true
            anchors {
                verticalCenter: parent.verticalCenter
                right: parent.right
                rightMargin: _units.grid_unit
            }
        }
        Rectangle {
            id: topRounding
            visible: root.isTop
            height: _units.small_spacing
            color: palette.window
            clip: true
            anchors {
                left: parent.left
                right: parent.right
                top: parent.top
            }
            Rectangle {
                height: Math.round(_units.grid_unit / 2)
                radius: 5
                color: root.color
                border {
                    color: Qt.darker(palette.window, 1.2)
                    width: 1
                }
                anchors {
                    left: parent.left
                    right: parent.right
                    top: parent.top
                }
            }
        }
        Rectangle {
            id: bottomRounding
            visible: root.isBottom
            height: _units.small_spacing
            color: palette.window
            clip: true
            anchors {
                left: parent.left
                right: parent.right
                bottom: parent.bottom
            }
            Rectangle {
                height: Math.round(_units.grid_unit / 2)
                radius: 5
                color: root.color
                border {
                    color: Qt.darker(palette.window, 1.2)
                    width: 1
                }
                anchors {
                    left: parent.left
                    right: parent.right
                    bottom: parent.bottom
                }
            }
        }
        FocusRectangle {
            visible: root.activeFocus
            anchors.fill: parent
            anchors.margins: _units.small_spacing
        }
    }

    Keys.onSpacePressed: delegateMouse.action()
    MouseArea {
        id: delegateMouse
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        function action() {
            //if (release.isLocal) {
            if (false) {
                releases.selectedIndex = index
                fileDialog.visible = true
            }
            else {
                imageList.currentIndex = index
                imageList.stepForward(release.index)
            }
        }
        onClicked: {
            action()
        }
    }
}