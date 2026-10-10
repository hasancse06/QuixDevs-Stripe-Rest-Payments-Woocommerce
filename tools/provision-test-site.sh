#!/usr/bin/env bash
# Provision only an explicitly named empty/disposable test database.
set -euo pipefail
: "${QUIXDEVS_WP_ROOT:?Set an empty temporary WordPress directory}"
: "${QUIXDEVS_DB_HOST:?Set a private test MySQL host/socket}"
: "${QUIXDEVS_DB_USER:?Set a test DB user}"
: "${QUIXDEVS_DB_PASSWORD:=}"
: "${QUIXDEVS_DISPOSABLE_TESTS:?Set to 1 to acknowledge disposable tests}"
[[ "$QUIXDEVS_DISPOSABLE_TESTS" == 1 && "$QUIXDEVS_WP_ROOT" == *quixdevs* && "$QUIXDEVS_DB_HOST" == *quixdevs* ]] || exit 2
: "${WP_CLI:=wp}"
: "${QUIXDEVS_WP_VERSION:=6.9}"
: "${QUIXDEVS_WC_VERSION:=10.9.0}"
: "${QUIXDEVS_STRIPE_VERSION:=11.0.1}"
if [[ -f "$QUIXDEVS_WP_ROOT/wp-config.php" ]]; then echo 'Refusing to overwrite existing WordPress config'; exit 2; fi
mkdir -p "$QUIXDEVS_WP_ROOT"
"$WP_CLI" core download --path="$QUIXDEVS_WP_ROOT" --version="$QUIXDEVS_WP_VERSION"
"$WP_CLI" config create --path="$QUIXDEVS_WP_ROOT" --dbname=quixdevs_test --dbuser="$QUIXDEVS_DB_USER" --dbpass="$QUIXDEVS_DB_PASSWORD" --dbhost="$QUIXDEVS_DB_HOST"
"$WP_CLI" core install --path="$QUIXDEVS_WP_ROOT" --url=https://quixdevs.test --title='QuixDevs disposable tests' --admin_user=quixdevs_test_admin --admin_password=temporary-local-fixture-password --admin_email=admin@example.test --skip-email
"$WP_CLI" plugin install woocommerce --version="$QUIXDEVS_WC_VERSION" --path="$QUIXDEVS_WP_ROOT" --activate
"$WP_CLI" plugin install woocommerce-gateway-stripe --version="$QUIXDEVS_STRIPE_VERSION" --path="$QUIXDEVS_WP_ROOT"
"$WP_CLI" plugin install plugin-check --path="$QUIXDEVS_WP_ROOT"
mkdir -p "$QUIXDEVS_WP_ROOT/wp-content/mu-plugins"
cp tests/fixtures/network.php "$QUIXDEVS_WP_ROOT/wp-content/mu-plugins/quixdevs-test-network.php"
ln -s "$PWD" "$QUIXDEVS_WP_ROOT/wp-content/plugins/quixdevs-stripe-rest-payments"
"$WP_CLI" plugin activate woocommerce-gateway-stripe --path="$QUIXDEVS_WP_ROOT"
"$WP_CLI" option update woocommerce_stripe_settings '{"enabled":"yes","testmode":"yes","test_publishable_key":"pk_test_quixdevs_dummy","test_secret_key":"sk_test_quixdevs_dummy","upe_checkout_experience_enabled":"yes","upe_checkout_experience_accepted_payments":["card"]}' --format=json --path="$QUIXDEVS_WP_ROOT"
"$WP_CLI" plugin activate quixdevs-stripe-rest-payments --path="$QUIXDEVS_WP_ROOT"
