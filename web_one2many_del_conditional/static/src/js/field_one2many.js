/* Copyright 2022 Maged Ibrahem */
odoo.define("web.web_one2many_del_conditional", function(require) {
    "use strict";

    var ListRenderer = require('web.ListRenderer');

    ListRenderer.include({
        _renderRow: function(record, index) {
            var $row = this._super.apply(this, arguments);
            if (this.addTrashIcon) {
                var state = record.data.state
                if (state != undefined) {
                    if (_.has(record.fieldsInfo.list.state, 'delete')) {
                        var del_state = record.fieldsInfo.list.state.delete
                        if (state != del_state) {
                            $row.find(".o_list_record_remove").removeClass("o_list_record_remove").empty();
                        }
                    }
                }
            }
            return $row;
        },

    });

});