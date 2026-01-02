from rest_framework import serializers
from payroll.models.benefits_models import TaxConfiguration
from django.db.models import Q
from decimal import Decimal


class TaxConfigurationSerializer(serializers.ModelSerializer):

    class Meta:
        model = TaxConfiguration
        fields = "__all__"

    def validate(self, data):
        min_amt = data.get("min_amount")
        max_amt = data.get("max_amount")
        is_active = data.get("is_active", False)

        # -----------------------------------
        # 1️⃣ Basic sanity checks
        # -----------------------------------
        if min_amt is None or max_amt is None:
            raise serializers.ValidationError(
                "Both min_amount and max_amount are required."
            )

        if min_amt < 0 or max_amt < 0:
            raise serializers.ValidationError(
                "Tax slab amounts cannot be negative."
            )

        if min_amt >= max_amt:
            raise serializers.ValidationError(
                "min_amount must be less than max_amount."
            )

        # -----------------------------------
        # 2️⃣ Prevent overlapping slabs
        # -----------------------------------
        qs = TaxConfiguration.objects.filter(
            deleted_at__isnull=True
        )

        if self.instance:
            qs = qs.exclude(id=self.instance.id)

        overlap = qs.filter(
            Q(min_amount__lt=max_amt) &
            Q(max_amount__gt=min_amt)
        ).exists()

        if overlap:
            raise serializers.ValidationError(
                "Tax slab overlaps with an existing slab."
            )

        # -----------------------------------
        # 3️⃣ Enforce continuity (no gaps)
        # -----------------------------------
        slabs = qs.order_by("min_amount")

        previous_max = None
        for slab in slabs:
            if previous_max is not None:
                if slab.min_amount != previous_max:
                    raise serializers.ValidationError(
                        "Tax slabs must be continuous without gaps."
                    )
            previous_max = slab.max_amount

        # -----------------------------------
        # 4️⃣ Only ONE active slab set
        # -----------------------------------
        if is_active:
            active_exists = TaxConfiguration.objects.filter(
                is_active=True,
                deleted_at__isnull=True
            )

            if self.instance:
                active_exists = active_exists.exclude(id=self.instance.id)

            if active_exists.exists():
                raise serializers.ValidationError(
                    "Another active tax configuration already exists. "
                    "Deactivate it before activating a new one."
                )

        return data
