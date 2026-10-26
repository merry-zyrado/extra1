/** @odoo-module **/

import { registry } from "@web/core/registry";
import { AppBoard } from "./app_board";
import { EventBus } from "@odoo/owl";


export const MnkAppBoardService = {
    dependencies: ["menu"],

    start() {
        const bus = new EventBus();
        registry.category("main_components").add("mnkAppBoard", {
            Component: AppBoard,
            props: {
                bus: bus
            },
        });

        return {
            show: () => {
                bus.trigger("ShowAppBoard");
            },

            hide: () => {
                bus.trigger("HideAppBoard");
            }
        }
    }
};

registry.category("services").add("mnk_app_board", MnkAppBoardService);
