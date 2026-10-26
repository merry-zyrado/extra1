/** @odoo-module **/

import { Component, useState} from "@odoo/owl";
import { bus, _t } from 'web.core';
import { useService } from "@web/core/utils/hooks";

import { AppItem } from "./app_item";

export class AppBar extends Component {

    setup() {
        
        this.currentAppSectionsExtra = [];

        this.actionService = useService("action");
        this.menuService = useService("menu");

        // add the active app
        var apps = this.menuService.getApps();

        // deal appp datas
        apps.forEach(app => {
            let imgtype = 'png'
            // check if webIcon is svg
            if (app.webIcon && _.str.endsWith(app.webIcon, '.svg')) {
                imgtype = 'svg+xml'
            }
            app['webIconData'] = `data:image/${imgtype};base64,${app['webIconData']}`
        })

        // get all menus
        this.state = useState({ apps });
    }

    willUnmount() {
        this.env.bus.off("MENUS:APP-CHANGED", this);
    }
}

AppBar.components = { AppItem };
AppBar.props = {};
AppBar.template = 'mnk_theme.app_bar';
