/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Many2XAutocomplete } from "@web/views/fields/relational_utils";
import { _t } from "@web/core/l10n/translation";


patch(Many2XAutocomplete.prototype, {
    async onSearchMore(request) {
        console.log('111111111111111111111111111111111111111111');
        const { resModel, getDomain, context, fieldString } = this.props;

        const domain = getDomain();
        let dynamicFilters = [];
        if (request.length) {
            const nameGets = await this.orm.call(resModel, "name_search", [], {
                name: request,
                args: domain,
                operator: "ilike",
                limit: this.props.searchMoreLimit,
                context,
            });

            dynamicFilters = [
                {
                    description: _t("Quick search: %s", request),
                    domain: [["id", "in", nameGets.map((nameGet) => nameGet[0])]],
                },
            ];
        }

        const title = _t("Search: %s", fieldString);

        // ✅ Inject custom context flag here
        const extendedContext = {
            ...context,
            is_from_search_more: true,
        };

        this.selectCreate({
            domain,
            context: extendedContext,
            filters: dynamicFilters,
            title,
        });
    }
});
