from decimal import Decimal

class PlanChangePolicy(object):

    def _calculate_day_cost(self, plan, period):
        """
        Finds most fitted plan pricing for a given period, and calculate day cost
        """

        plan_pricings = plan.planpricing_set.order_by('-pricing__period').select_related('pricing')
        selected_pricing = None
        for plan_pricing in plan_pricings:
            selected_pricing = plan_pricing
            if plan_pricing.pricing.period <= period:
                break

        if selected_pricing:
            return (selected_pricing.price / selected_pricing.pricing.period).quantize(Decimal('1.00'))

        raise ValueError('Plan %s has no pricings.' % plan)

    def _calculate_final_price(self, period, day_cost_diff):
        if day_cost_diff is None:
            return None
        else:
            return period * day_cost_diff

    def get_change_price(self, plan_old, plan_new, period):
        """
        Calculates total price of plan change. Returns None if no payment is required.
        """
        if period < 1:
            return None

        plan_old_day_cost = self._calculate_day_cost(plan_old, period)
        plan_new_day_cost = self._calculate_day_cost(plan_new, period)

        if plan_new_day_cost <= plan_old_day_cost:
            return self._calculate_final_price(period, None)
        else:
            return self._calculate_final_price(period, plan_new_day_cost - plan_old_day_cost)



class StandardPlanChangePolicy(PlanChangePolicy):
    """
    This plan switch policy follows the rules:
    * user can downgrade a plan for free if the plan is cheaper or have exact the same price
    * user need to pay extra amount of price difference with additional upgrade rate percent fee
    """

    UPGRADE_PERCENT_RATE = Decimal('10.0')
    UPGRADE_CHARGE = Decimal('0.0')
    DOWNGRADE_CHARGE = None


    def _calculate_final_price(self, period, day_cost_diff):
        if day_cost_diff is None:
            return self.DOWNGRADE_CHARGE
        else:
            return (period * day_cost_diff * (self.UPGRADE_PERCENT_RATE/100 + 1) + self.UPGRADE_CHARGE).quantize(Decimal('1.00'))