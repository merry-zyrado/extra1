/** @odoo-module **/

import { useService } from "@web/core/utils/hooks";
import { isIosApp } from "@web/core/browser/feature_detection";
import { fuzzyLookup } from "@web/core/utils/search";
import { Component, useState, useExternalListener, useRef, useEffect } from "@odoo/owl";

function traverseMenuTree(tree, cb, parents = []) {
    cb(tree, parents);
    tree.childrenTree.forEach((c) => traverseMenuTree(c, cb, parents.concat([tree])));
}

function computeAppsAndMenuItems(menuTree) {
    const apps = [];
    const menuItems = [];
    traverseMenuTree(menuTree, (menuItem, parents) => {
        if (!menuItem.id || !menuItem.actionID) {
            return;
        }
        const isApp = menuItem.id === menuItem.appID;
        const item = {
            parents: parents
                .slice(1)
                .map((p) => p.name)
                .join(" / "),
            label: menuItem.name,
            id: menuItem.id,
            xmlid: menuItem.xmlid,
            actionID: menuItem.actionID,
            appID: menuItem.appID,
        };
        if (isApp) {
            if (menuItem.webIconData) {
                item.webIconData = menuItem.webIconData;
            } else {
                const [iconClass, color, backgroundColor] = (menuItem.webIcon || "").split(",");
                if (backgroundColor !== undefined) {
                    item.webIcon = { iconClass, color, backgroundColor };
                } else {
                    item.webIconData = "/mnk_theme/static/img/default_icon_app.png";
                }
            }
        } else {
            item.menuID = parents[1].id;
        }
        if (isApp) {
            apps.push(item);
        } else {
            menuItems.push(item);
        }
    });
    return { apps, menuItems };
}


export class AppBoard extends Component {

    setup() {
        super.setup();

        this.menus = useService("menu");
        this.ui = useService("ui");

        this.inputRef = useRef("input");
        this.rootRef = useRef("root");

        let { apps, menuItems } = computeAppsAndMenuItems(this.menus.getMenuAsTree("root"));
        this.apps = apps;
        this.menuItems = menuItems;

        this.state = useState({
            visible: false,
            focusedIndex: null,
            isSearching: false,
            query: "",
            isIosApp: isIosApp(),
            availableApps: apps,
            displayedMenuItems: []
        });

        this.props.bus.on('ShowAppBoard', this, () => {
            this.show();
        })

        this.props.bus.on('HideAppBoard', this, () => {
            this.hide();
        })

        if (!this.env.isSmall) {
            useExternalListener(window, "keydown", this._onKeydown);
        }

        // bind the composit
        this.isComposing = false;
        useEffect(() => {
            this.inputRef.el.addEventListener('compositionstart', () => {
                this.isComposing = true;
            });
            this.inputRef.el.addEventListener('compositionend', () => {
                this.isComposing = false;
                // update query
                let text = this.inputRef.el.value
                this._updateQuery(text)
            });
        }, () => []);

        // if click outside the panel close it
        useExternalListener(window, 'click', (event) => {

            if ($(event.target).is($(".board_toggler, .board_toggler *"))) {
                return
            }

            if (this.rootRef.el.contains(event.target)) {
                return;
            }

            this.hide()
        });
    }

    show() {
        this.state.visible = true;
    }

    hide() {
        this.state.visible = false;
    }

    async willUpdateProps() {
        // State is reset on each remount
        this.state.focusedIndex = null;
        this.state.isSearching = false;
        this.state.query = "";
        this.inputRef.el.value = "";
    }

    patched() {
        if (this.state.focusedIndex !== null && !this.env.isSmall) {
            const selectedItem = document.querySelector(".mkn_app_board .o_menuitem.o_focused");
            // When TAB is managed externally the class o_focused disappears.
            if (selectedItem) {
                // Center window on the focused item
                selectedItem.scrollIntoView({ block: "center" });
                selectedItem.focus();
            }
        }
    }

    get appIndex() {
        const appLength = this.displayedApps.length;
        const focusedIndex = this.state.focusedIndex;
        return focusedIndex < appLength ? focusedIndex : null;
    }

    get displayedApps() {
        return this.state.availableApps;
    }

    get maxIconNumber() {
        const w = window.innerWidth;
        if (w < 576) {
            return 3;
        } else if (w < 768) {
            return 4;
        } else {
            return 6;
        }
    }

    get menuIndex() {
        const appLength = this.displayedApps.length;
        const focusedIndex = this.state.focusedIndex;
        return focusedIndex >= appLength ? focusedIndex - appLength : null;
    }

    _filter(array) {
        return fuzzyLookup(this.state.query, array, (el) =>
            (el.parents + " / " + el.label).split("/").reverse().join("/")
        );
    }

    _openMenu(menu) {
        return this.menus.selectMenu(menu);
    }

    _updateFocusedIndex(cmd) {

        if (!this.state.visible) {
            return
        }

        const nbrApps = this.displayedApps.length;
        const nbrMenuItems = this.state.displayedMenuItems.length;
        const lastIndex = nbrApps + nbrMenuItems - 1;
        let oldIndex = this.state.focusedIndex;
        if (lastIndex < 0) {
            return;
        }
        if (!this.state.isSearching) {
            if (document.activeElement.classList.contains("o_menuitem")) {
                oldIndex = [...this.el.getElementsByClassName("o_menuitem")].indexOf(
                    document.activeElement
                );
            } else {
                this.el.getElementsByClassName("o_menuitem")[0].focus();
                return;
            }
        }
        const appIndex = this.state.isSearching ? this.appIndex : oldIndex;
        const lastAppIndex = nbrApps - 1;
        const appFocused = appIndex !== null;
        const lineNumber = Math.ceil(nbrApps / this.maxIconNumber);
        const currentLine = appFocused ? Math.ceil((appIndex + 1) / this.maxIconNumber) : null;
        let newIndex;
        switch (cmd) {
            case "previousElem":
                newIndex = oldIndex - 1;
                break;
            case "nextElem":
                newIndex = oldIndex + 1;
                break;
            case "previousColumn":
                if (!appFocused) {
                    newIndex = oldIndex;
                } else if (oldIndex % this.maxIconNumber) {
                    // app is not the first one on its line
                    newIndex = oldIndex - 1;
                } else {
                    newIndex = oldIndex + Math.min(lastAppIndex - oldIndex, this.maxIconNumber - 1);
                }
                break;
            case "nextColumn":
                if (!appFocused) {
                    newIndex = oldIndex;
                } else if (oldIndex === lastAppIndex || (oldIndex + 1) % this.maxIconNumber === 0) {
                    // app is the last one on its line
                    newIndex = (currentLine - 1) * this.maxIconNumber;
                } else {
                    newIndex = oldIndex + 1;
                }
                break;
            case "previousLine":
                if (!appFocused) {
                    if (oldIndex > lastAppIndex + 1) {
                        // there is a menu item 'above' -> select it
                        newIndex = oldIndex - 1;
                    } else {
                        // select first app of last line
                        newIndex = (lineNumber - 1) * this.maxIconNumber;
                    }
                } else if (currentLine === 1) {
                    // app is in first line
                    if (nbrMenuItems > 0) {
                        // there is at least a menu item -> select the last one
                        newIndex = lastIndex;
                    } else {
                        // no menu item -> select the app in the closest column on last line
                        newIndex = oldIndex + (lineNumber - 1) * this.maxIconNumber;
                        if (newIndex > lastAppIndex) {
                            newIndex = lastAppIndex;
                        }
                    }
                } else {
                    // we go to the previous line on same column
                    newIndex = oldIndex - this.maxIconNumber;
                }
                break;
            case "nextLine":
                if (!appFocused) {
                    newIndex = oldIndex + 1;
                } else if (currentLine === lineNumber) {
                    // app is in last line
                    if (nbrMenuItems > 0) {
                        // there is at least a menu item -> select the first one
                        newIndex = lastAppIndex + 1;
                    } else {
                        // no menu item -> select the app in the same column on first line
                        newIndex = oldIndex % this.maxIconNumber;
                    }
                } else {
                    // we go to the next line on the closest column
                    newIndex = oldIndex + Math.min(this.maxIconNumber, lastAppIndex - oldIndex);
                }
                break;
        }
        // if newIndex is out of bounds -> normalize it
        if (newIndex < 0) {
            newIndex = lastIndex;
        } else if (newIndex > lastIndex) {
            newIndex = 0;
        }
        if (this.state.isSearching) {
            this.state.focusedIndex = newIndex;
        } else {
            const item = this.el.getElementsByClassName("o_menuitem")[newIndex];
            item.focus();
        }
    }

    _updateQuery(query) {

        if (this.isComposing) {
            return
        }

        this.state.query = query;
        this.inputRef.el.value = this.state.query;
        this.state.isSearching = true;

        if (query === "") {
            this.state.availableApps = this.apps;
            this.state.displayedMenuItems = [];
        } else {
            this.state.availableApps = this._filter(this.apps);
            this.state.displayedMenuItems = this._filter(this.menuItems);
        }
        const total = this.displayedApps.length + this.state.displayedMenuItems.length;
        this.state.focusedIndex = total ? 0 : null;
    }

    _onAppClick(app) {
        this._openMenu(app);
        this.hide();
    }

    _onInputSearch(ev) {
        this._updateQuery(ev.target.value);
    }

    _onKeydown(ev) {
    
        const isEditable =
            ev.target.tagName === "INPUT" ||
            ev.target.tagName === "TEXTAREA" ||
            ev.target.isContentEditable;

        const input = this.inputRef.el;
        if (isEditable && ev.target !== input) {
            return;
        }

        if (this.ui.activeElement !== document) {
            return;
        }

        switch (ev.key) {
            case "ArrowDown":
                this._updateFocusedIndex("nextLine");
                ev.preventDefault();
                break;
            case "ArrowRight":
                if (
                    input === document.activeElement &&
                    input.selectionEnd < this.state.query.length
                ) {
                    return;
                }
                this._updateFocusedIndex("nextColumn");
                ev.preventDefault();
                break;
            case "ArrowUp":
                this._updateFocusedIndex("previousLine");
                ev.preventDefault();
                break;
            case "ArrowLeft":
                if (input === document.activeElement && input.selectionStart > 0) {
                    return;
                }
                this._updateFocusedIndex("previousColumn");
                ev.preventDefault();
                break;
            case "Tab":
                if (!this.state.isSearching) {
                    return;
                }
                ev.preventDefault();
                this._updateFocusedIndex(ev.shiftKey ? "previousElem" : "nextElem");
                break;
            case "Enter":
                if (this.state.focusedIndex !== null) {
                    const isApp = this.appIndex !== null;
                    const menu = isApp
                        ? this.displayedApps[this.appIndex]
                        : this.state.displayedMenuItems[this.menuIndex];
                    this._openMenu(menu);
                    this.hide();
                    ev.preventDefault();
                }
                return;
            case "Alt":
            case "AltGraph":
            case "Control":
            case "Meta":
            case "PageDown":
            case "PageUp":
            case "Shift":
                break;

            case "Escape": {
                const currentQuery = this.state.query;
                if (currentQuery) {
                    this._updateQuery("");
                } else {
                    this.hide();
                }
                break;
            }

            case "c":
            case "x":
                if (ev.ctrlKey || ev.metaKey) {
                    break;
                }

            default:
                if (document.activeElement !== input) {
                    input.focus();
                }
        }
    }

    _onMenuitemClick(menu) {
        this._openMenu(menu);
    }
}

AppBoard.components = {};
AppBoard.props = {
    bus: {
        type: Object
    }
};

AppBoard.template = "mnk_theme.app_board";
