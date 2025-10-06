def _make_unique_effect_handlers(self):
    """Creates a dictionary of effect handlers as closures. Each closure captures self and can access instance state."""
    return {

        CardUniqueEffect.effect_bonus_if_min_bond:
        # unique_effect_id = 101
        # value=min_bond, value_1=effect_id, value_2=bonus_amount
        # sample card: 30189-kitasan-black
            lambda vals: [
                (
                    CardEffect(vals[1]),
                    vals[2] * (self.turn.card_bonds[self.card] >= vals[0])
                )
            ],

        CardUniqueEffect.effect_bonus_per_combined_bond:
        # unique_effect_id = 109
        # value = effect_id, value_1 = max_bonus
        # sample card: 30208-nishino-flower
            lambda vals: [
                (
                    CardEffect(vals[0]),
                    20 + self.turn.combined_bond_gauge // vals[1]
                )
            ],
        
        CardUniqueEffect.effect_bonus_per_facility_level:
        # unique_effect_id = 111
        # value = effect_id, value_1 = bonus_amount
        # sample card: 30107-maruzensky
            lambda vals: [
                (
                    CardEffect(vals[0]),
                    self.turn.facility_levels[self.facility_type] * vals[1]
                )
            ],
        
        CardUniqueEffect.effect_bonus_if_friendship_training:
        # unique_effect_id = 113
        # value = effect_id, value_1 = bonus_amount
        # sample card: 30256-tamamo-cross
            lambda vals: [
                (
                    CardEffect(vals[0]),
                    vals[1] * self.card.is_preferred_facility(self.facility_type)
                )
            ],
        
        CardUniqueEffect.effect_bonus_on_more_energy:
        # unique_effect_id = 114
        # value = effect_id, value_1 = energy_per_bonus_point, value_2 = max_bonus
        # sample card: 30115-mejiro-palmer
            lambda vals: [
                (
                    CardEffect(vals[0]),
                    min(self.turn.energy // vals[1], vals[2])
                )
            ],
        
        CardUniqueEffect.effect_bonus_on_less_energy:
        # unique_effect_id = 107
        # value = effect_id, value_1 = energy_per_bonus_point, value_2 = energy_floor, value_3 = max_bonus, value_4 = base_bonus
        # sample card: 30094-bamboo-memory
            lambda vals: [
                (
                    CardEffect(vals[0]),
                    min(vals[3], vals[4] + (self.turn.max_energy - max(self.turn.energy, vals[2])) // vals[1]) * (self.turn.energy <= 100)
                )
            ],

        CardUniqueEffect.effect_bonus_on_more_max_energy:
        # unique_effect_id = 108
        # value=effect_id, value_1=?, value_2=?, value_3=min_bonus?, value_4=max_bonus?
        # TODO: Formula unclear - needs testing with actual card
        # Temporarily returns max_bonus until proper implementation can be verified
        # sample card: 30095-seeking-the-pearl
            lambda vals: (
                logger.warning(f"Card {self.card.id} uses effect_bonus_on_more_max_energy (108) which has an unverified implementation"),
                [
                    (
                        CardEffect(vals[0]),
                        vals[4]  # Always return max_bonus (20) until formula is confirmed
                    )
                ]
            )[1],

        CardUniqueEffect.extra_appearance_if_min_bond:
        # unique_effect_id = 118
        # value = extra_appearances, value_1 = min_bond
        # sample card: 30160-mei-satake
        # Not used in simulator - return empty list
            lambda vals: [],

        CardUniqueEffect.cards_appear_more_if_min_bond:
        # unique_effect_id = 119
        # value = ?, value_1 = ?, value_2 = min_bond
        # sample card: 30188-ryoka-tsurugi
        # Not used in simulator - return empty list
            lambda vals: [],

        CardUniqueEffect.all_cards_gain_bond_bonus_per_training:
        # unique_effect_id = 121
        # value = bonus_amount, value_1 = bonus_amount_if_card_on_facility
        # sample card: 30207-yayoi-akikawa
        # Affects other cards - not tracked in simulator
            lambda vals: [],

        CardUniqueEffect.cards_gain_effect_bonus_next_turn_after_trained_with:
        # unique_effect_id = 122
        # value = effect_id, value_1 = bonus_amount
        # sample card: 30257-tucker-bryne
        # Requires turn-by-turn tracking - too complex for simulator
            lambda vals: [],

        CardUniqueEffect.training_effectiveness_if_min_card_types:
        # unique_effect_id = 103
        # value = min_card_types, value_1 = bonus_amount
        # sample card: 30250-buena-vista
        # Bonus if number of different card types on facility >= threshold
            lambda vals: [
                (
                    CardEffect.training_effectiveness,
                    vals[1] * (self.turn.card_types_in_deck >= vals[0])
                )
            ],

        CardUniqueEffect.training_effectiveness_for_fans:
        # unique_effect_id = 104
        # value = fans_per_bonus, value_1 = max_bonus_amount
        # sample card: 30086-narita-top-road
            lambda vals: [
                (
                    CardEffect.training_effectiveness,
                    min(vals[1], self.turn.fan_count // vals[0])
                )
            ],

        CardUniqueEffect.training_effectiveness_if_min_bond_and_not_preferred_facility:
        # unique_effect_id = 102
        # value = min_bond, value_1 = bonus_amount
        # sample card: 30083-sakura-bakushin-o
            lambda vals: [
                (
                    CardEffect.training_effectiveness,
                    vals[1] * (self.turn.card_bonds[self.card] >= vals[0] and not self.card.is_preferred_facility(self.facility_type))
                )
            ],

        CardUniqueEffect.effect_bonus_per_friendship_trainings:
        # unique_effect_id = 106
        # value=max_times, value_1 = effect_id, value_2 = bonus_amount
        # sample card: 30112-twin-turbo
        # Bonus per friendship trainings done (assumes max_times if bond is enough to trigger them)
            lambda vals: [
                (
                    CardEffect(vals[1]),
                    vals[2] * vals[0] * (self.turn.card_bonds[self.card] >= CardConstants.FRIENDSHIP_BOND_THRESHOLD)
                )
            ],

        CardUniqueEffect.effect_bonus_per_card_on_facility:
        # unique_effect_id = 110
        # value = effect_id, value_1 = bonus_amount
        # sample card: 30102-el-condor-pasa
            lambda vals: [
                (
                    CardEffect(vals[0]),
                    (self.turn.get_card_count(facility_type=self.facility_type) - 1) * vals[1]
                )
            ],

        CardUniqueEffect.chance_for_no_failure:
        # unique_effect_id = 112
        # value = chance
        # sample card: 30108-nakayama-festa
        # Not used in simulator - return empty list
            lambda vals: [],

        CardUniqueEffect.all_cards_gain_effect_bonus:
        # unique_effect_id = 115
        # value = effect_id, value_1 = bonus_amount
        # sample card: 30146-oguri-cap
        # Affects other cards - not tracked in simulator
            lambda vals: [],

        CardUniqueEffect.effect_bonus_per_skill_type:
        # unique_effect_id = 116
        # value = skill_type, value_1 = effect_id, value_2 = bonus_amount, value_3 = max_skills_count
        # sample card: 30134-mejiro-ramonu
            lambda vals: [
                (
                    CardEffect(vals[1]),
                    min(self.turn.get_skill_count(SkillType(vals[0])), vals[3]) * vals[2]
                )
            ],

        CardUniqueEffect.stat_up_per_card_based_on_type:
        # unique_effect_id = 105
        # value=stat_amount_per_matching_stat_card, value_1=all_stats_amount_per_non_stat_card
        # sample card: 30090-symboli-rudolf
        # Provides initial stats at start of run based on deck composition
        # Not tracked in training simulator - affects only starting stats
            lambda vals: [],

        CardUniqueEffect.effect_bonus_per_combined_facility_level:
        # unique_effect_id = 117
        # value = effect_id, value_1 = target_combined_level, value_2 = max_bonus
        # sample card: 30148-daiwa-scarlet
            lambda vals: [
                (
                    CardEffect(vals[0]),
                    vals[2] * self.turn.combined_facility_levels // vals[1]
                )
            ],

        CardUniqueEffect.stat_or_skill_points_bonus_per_card_based_on_type:
        # unique_effect_id = 120
        # value = skill_point_bonus_per_pal, value_1 = min_bond, value_2 = stat_bonus_per_stat_type, value_3 = max_cards_per_stat
        # sample card: 30187-orfevre
            lambda vals: [
                # Speed bonus (effect 3)
                (
                    CardEffect(3), 
                    min(self.turn.get_card_count(card_type=CardType.SPEED), vals[3]) 
                    * vals[2] 
                    * (self.turn.card_bonds[self.card] >= vals[1])
                ),
                # Stamina bonus (effect 4)
                (
                    CardEffect(4), 
                    min(self.turn.get_card_count(card_type=CardType.STAMINA), vals[3]) 
                    * vals[2] 
                    * (self.turn.card_bonds[self.card] >= vals[1])
                ),
                # Power bonus (effect 5)
                (
                    CardEffect(5), 
                    min(self.turn.get_card_count(card_type=CardType.POWER), vals[3]) 
                    * vals[2] 
                    * (self.turn.card_bonds[self.card] >= vals[1])
                ),
                # Guts bonus (effect 6)
                (
                    CardEffect(6), 
                    min(self.turn.get_card_count(card_type=CardType.GUTS), vals[3]) 
                    * vals[2] 
                    * (self.turn.card_bonds[self.card] >= vals[1])
                ),
                # Wit bonus (effect 7)
                (
                    CardEffect(7), 
                    min(self.turn.get_card_count(card_type=CardType.WIT), vals[3]) 
                    * vals[2] 
                    * (self.turn.card_bonds[self.card] >= vals[1])
                ),
                # Skill points (effect 30) - no cap on Pal cards
                (
                    CardEffect(30), 
                    self.turn.get_card_count(card_type=CardType.PAL) 
                    * vals[0] 
                    * (self.turn.card_bonds[self.card] >= vals[1])
                )
            ],

        # Add unique effects handlers here as they are added to the game
        # See: https://umamusu.wiki/Game:List_of_Support_Cards
    }
