<?php
/**
 * LocalSettings.php — Wikimedica MediaWiki Configuration Example
 *
 * USAGE:
 *   Copy this file to LocalSettings.php and replace all REPLACE_WITH_* placeholders
 *   with actual values from your .env file.
 *
 *   In production, this file is generated from environment variables.
 *   NEVER commit LocalSettings.php with real credentials to version control.
 *
 * SECURITY:
 *   - This file must not be web-accessible.
 *   - Keep $wgSecretKey and $wgDBpassword secret at all times.
 *   - File permissions: chmod 640 LocalSettings.php
 *
 * See: https://www.mediawiki.org/wiki/Manual:LocalSettings.php
 */

# =============================================================================
# Path & URL Configuration
# =============================================================================

## The URL base path to the directory containing the wiki.
$wgScriptPath = "";

## The protocol and server name to use in fully-qualified URLs.
$wgServer = "https://REPLACE_WITH_DOMAIN";  # e.g. https://wikimedica.de

## The URL path to static resources (images, scripts, etc.)
$wgResourceBasePath = $wgScriptPath;

## The URL path for the logo.
$wgLogos = [
    '1x' => "$wgResourceBasePath/resources/assets/wikimedica-logo.png",
    'icon' => "$wgResourceBasePath/resources/assets/wikimedica-icon.png",
];

# =============================================================================
# Site Identity
# =============================================================================

$wgSitename = "Wikimedica";
$wgMetaNamespace = "Wikimedica";

## Default language of the wiki — German.
$wgLanguageCode = "de";

## Site contact email address.
$wgEmergencyContact = "tech@wikimedica.de";
$wgPasswordSender = "noreply@wikimedica.de";

# =============================================================================
# Database Configuration
# =============================================================================

$wgDBtype = "mysql";
$wgDBserver = getenv('MEDIAWIKI_DB_HOST') ?: "mariadb";
$wgDBname = getenv('MEDIAWIKI_DB_NAME') ?: "wikimedica";
$wgDBuser = getenv('MEDIAWIKI_DB_USER') ?: "wikimedica_app";
$wgDBpassword = getenv('MEDIAWIKI_DB_PASSWORD') ?: "REPLACE_WITH_DB_PASSWORD";

## MySQL specific settings.
$wgDBprefix = "";

## MySQL table options to use during installation or updates.
$wgDBTableOptions = "ENGINE=InnoDB, DEFAULT CHARSET=binary";

# =============================================================================
# Security & Secrets
# =============================================================================

## This is a secret key for HMAC-based authentication of login cookies.
## Generate with: openssl rand -hex 32
$wgSecretKey = getenv('MEDIAWIKI_SECRET_KEY') ?: "REPLACE_WITH_64_CHAR_SECRET_KEY";

## An internal secret used to modify MediaWiki's page/revision upgrade key.
$wgUpgradeKey = getenv('MEDIAWIKI_UPGRADE_KEY') ?: "REPLACE_WITH_16_CHAR_UPGRADE_KEY";

# =============================================================================
# Cache Configuration
# =============================================================================

## Shared memory settings.
## Default: APCu (CACHE_ACCEL) for the main cache; DB for the parser cache.
$wgMainCacheType = CACHE_ACCEL;  # Use APCu/opcache if available
$wgMessageCacheType = CACHE_ACCEL;
$wgParserCacheType = CACHE_DB;   # Or CACHE_REDIS if the Redis service is enabled

## OPTIONAL — Redis object cache & job queue (see version-policy.md DEC-3).
## Enable together with the `redis` service in docker-compose.yml.
# $wgObjectCaches['redis'] = [
#     'class'   => 'RedisBagOStuff',
#     'servers' => [ getenv('REDIS_HOST') ?: 'redis:6379' ],
# ];
# $wgMainCacheType   = 'redis';
# $wgParserCacheType = 'redis';
# $wgJobTypeConf['default'] = [ 'class' => 'JobQueueRedis', 'redisServer' => getenv('REDIS_HOST') ?: 'redis:6379', 'redisConfig' => [] ];

## Specify a different path for cache files.
## NOTE: use a literal path — do NOT reference $wgUploadDirectory here, it is
## defined further below and would be empty at this point.
$wgFileCacheDirectory = "/var/www/html/images/cache";

# =============================================================================
# Images and File Uploads
# =============================================================================

## To enable image uploads, make sure the 'images' directory is web-accessible.
$wgEnableUploads = true;
$wgUploadDirectory = "/var/www/html/images";
$wgUploadPath = "$wgScriptPath/images";

## Allowed file extensions for uploads.
$wgFileExtensions = array_merge(
    $wgFileExtensions,
    ['svg', 'webp', 'pdf']
);

## Max upload file size (in bytes) — 10 MB default.
$wgMaxUploadSize = 10 * 1024 * 1024;

## --- Upload security hardening (REQUIRED because svg/pdf/webp are allowed) ---
## Verify the real MIME type of every upload; never trust the extension alone.
$wgVerifyMimeType  = true;
$wgCheckFileExtensions   = true;
$wgStrictFileExtensions  = true;
$wgDisableUploadScriptChecks = false;

## Hard block of dangerous / executable types regardless of the allow-list.
$wgProhibitedFileExtensions = array_merge(
    $wgProhibitedFileExtensions ?? [],
    ['html', 'htm', 'xhtml', 'xml', 'js', 'php', 'phtml', 'phar', 'exe', 'sh']
);
$wgMimeTypeExclusions = array_merge(
    $wgMimeTypeExclusions ?? [],
    ['text/html', 'application/x-php', 'application/xhtml+xml', 'image/svg']
);

## SVG safety: rasterise/sanitise via a converter and forbid scripts/titles in SVG.
$wgAllowTitlesInSVG = false;
$wgSVGConverter = 'rsvg';   # ensure librsvg2-bin is present in the image/host
$wgSVGConverters = [
    'rsvg' => '$path/rsvg-convert -w $width -h $height -o $output $input',
];

## Antivirus scanning of uploads (enable where ClamAV is available).
# $wgAntivirus = 'clamav';
# $wgAntivirusSetup = [ 'clamav' => [ 'command' => 'clamscan --no-summary ', ... ] ];

# =============================================================================
# User Account Policies
# =============================================================================

## Who can create accounts.
## For a moderated contributor model, restrict registration.
$wgGroupPermissions['*']['createaccount'] = false;

## Who can edit pages without logging in.
$wgGroupPermissions['*']['edit'] = false;

## Allow users to read all pages.
$wgGroupPermissions['*']['read'] = true;

# -----------------------------------------------------------------------------
# Roles and rights  (see docs/editorial/roles-and-permissions.md)
# -----------------------------------------------------------------------------
## GitHub is the source of truth: article pages are WRITTEN BY THE IMPORT BOT
## ONLY. A manual wiki edit of an article would be overwritten by the next
## import, so human accounts get no write access to content namespaces.

## Anonymous: read-only.
$wgGroupPermissions['*']['createpage'] = false;
$wgGroupPermissions['*']['createtalk'] = false;

## Registered but unprivileged accounts: read-only as well.
foreach ( [ 'user', 'autoconfirmed' ] as $group ) {
    foreach ( [
        'edit', 'createpage', 'createtalk', 'minoredit',
        'move', 'move-subpages', 'move-rootuserpages', 'movefile',
        'upload', 'reupload', 'reupload-own', 'reupload-shared', 'upload_by_url',
    ] as $right ) {
        $wgGroupPermissions[$group][$right] = false;
    }
}

## Content namespaces need the custom right `wm-edit-content`, held only by the
## import bot and administrators.
$wgAvailableRights[] = 'wm-edit-content';
## IMPORTANT: bot passwords intersect the user's rights with their GRANTS. A custom right
## that belongs to no grant is silently dropped, and the import bot would be refused with
## "protectednamespace" (verified on MediaWiki 1.43.11). So attach it to the `editpage` grant.
$wgGrantPermissions['editpage']['wm-edit-content'] = true;
$wgGrantPermissionGroups['wm-edit-content'] = 'page-interaction';
foreach ( [ NS_MAIN, NS_TEMPLATE, NS_CATEGORY, NS_HELP, NS_PROJECT ] as $ns ) {
    $wgNamespaceProtection[$ns] = [ 'wm-edit-content' ];
}

## wm-editor: editorial staff may discuss on talk and user pages (feedback),
## but cannot touch content namespaces.
$wgGroupPermissions['wm-editor']['edit']       = true;
$wgGroupPermissions['wm-editor']['createtalk'] = true;
$wgGroupPermissions['wm-editor']['minoredit']  = true;

## wm-uploader: media upload is granted case by case (SVG/PDF/WebP are risky).
$wgGroupPermissions['wm-uploader']['upload']       = true;
$wgGroupPermissions['wm-uploader']['reupload-own'] = true;

## importbot: service account of scripts/publishing/import_to_mediawiki.py.
## Authenticate with a BotPassword (Special:BotPasswords) limited to these rights.
$wgGroupPermissions['importbot'] = [
    'read'            => true,
    'edit'            => true,
    'createpage'      => true,
    'minoredit'       => true,
    'bot'             => true,
    'apihighlimits'   => true,
    'wm-edit-content' => true,
];

## Administrators keep their working rights plus the content right.
## IMPORTANT: sysops normally inherit edit/upload/move from the 'user' group. Because those
## rights were removed from 'user' above, they must be granted to sysop EXPLICITLY — otherwise
## not even an administrator can edit the main page, MediaWiki:Common.css or system pages
## (verified on MediaWiki 1.43.11).
$wgGroupPermissions['sysop']['wm-edit-content'] = true;
$wgGroupPermissions['sysop']['createaccount']   = true;
foreach ( [
    'edit', 'createpage', 'createtalk', 'minoredit',
    'move', 'move-subpages', 'move-rootuserpages', 'movefile',
    'upload', 'reupload', 'reupload-own', 'reupload-shared',
] as $right ) {
    $wgGroupPermissions['sysop'][$right] = true;
}

## Restrictive group management: bureaucrats may only manage editorial groups.
## NOTE: $wgAddGroups / $wgRemoveGroups apply ONLY to users WITHOUT the
## `userrights` right, so it must be removed from the bureaucrat group.
## sysop/bureaucrat are assigned on the command line only:
##   php maintenance/createAndPromote.php --bureaucrat --sysop <user>
$wgGroupPermissions['bureaucrat']['userrights'] = false;
$wgAddGroups['bureaucrat']    = [ 'wm-editor', 'wm-uploader' ];
$wgRemoveGroups['bureaucrat'] = [ 'wm-editor', 'wm-uploader' ];
$wgAddGroups['sysop']    = [];
$wgRemoveGroups['sysop'] = [];

## Email confirmation required for editing.
$wgEmailConfirmToEdit = true;

## Require email address for account creation.
$wgEmailAuthentication = true;

# =============================================================================
# Email / SMTP
# =============================================================================
## Email must work for the "confirm email to edit" policy above. Configure an
## SMTP relay via environment variables (see .env.example SMTP_* block).
$wgEnableEmail = true;
$wgEnableUserEmail = true;
$wgEmailConfirmToEdit = true;

if ( getenv('SMTP_HOST') ) {
    $wgSMTP = [
        'host'     => getenv('SMTP_HOST'),
        'IDHost'   => getenv('SMTP_IDHOST') ?: 'wikimedica.de',
        'port'     => (int)( getenv('SMTP_PORT') ?: 587 ),
        'auth'     => true,
        'username' => getenv('SMTP_USER'),
        'password' => getenv('SMTP_PASSWORD'),
    ];
}

# =============================================================================
# Content Namespace Configuration
# =============================================================================

## Enable subpages in the main namespace.
$wgNamespacesWithSubpages[NS_MAIN] = true;

# =============================================================================
# Skin
# =============================================================================

## Default skin: Vector 2022 (modern responsive layout)
$wgDefaultSkin = "vector-2022";

## Installed skins.
wfLoadSkin( 'Vector' );
wfLoadSkin( 'MinervaNeue' );  # Optional: mobile skin

# =============================================================================
# Extensions
# =============================================================================

## Core editing tools
wfLoadExtension( 'WikiEditor' );          # Enhanced edit toolbar
wfLoadExtension( 'VisualEditor' );        # WYSIWYG editor

## Content structure and display
wfLoadExtension( 'CategoryTree' );        # Interactive category trees
wfLoadExtension( 'ParserFunctions' );     # Template logic functions
wfLoadExtension( 'Cite' );               # Footnote/reference system
## NOT bundled: TemplateStyles is missing from the MediaWiki 1.43 tarball and from the
## official Docker image — loading it here is a FATAL ERROR ("cannot be loaded") that takes
## the whole site down (verified on MediaWiki 1.43.11). It is optional (articles use no
## templates); enable it only in a custom image that installs the extension pinned to a
## REL1_43 commit (see docs/architecture/version-policy.md).
# wfLoadExtension( 'TemplateStyles' );      # Per-template CSS

## Code display
wfLoadExtension( 'SyntaxHighlight_GeSHi' );  # Syntax highlighting

## Navigation and search
wfLoadExtension( 'TitleBlacklist' );      # Prevent unwanted page titles

## User notifications
wfLoadExtension( 'Echo' );               # Notification system

## Anti-spam (important for a public wiki).
## 🧭 DEC-4: reCAPTCHA is wired below. A privacy-friendlier alternative is
## hCaptcha (ConfirmEdit/hCaptcha) — preferred for a German/EU audience; switch
## by loading that module instead and setting $wgHCaptchaSiteKey/SecretKey.
wfLoadExtension( 'ConfirmEdit' );
wfLoadExtension( 'ConfirmEdit/ReCaptchaNoCaptcha' );

# ReCaptcha keys (obtain from https://www.google.com/recaptcha/)
$wgReCaptchaSiteKey = getenv('RECAPTCHA_SITE_KEY') ?: "REPLACE_WITH_RECAPTCHA_SITE_KEY";
$wgReCaptchaSecretKey = getenv('RECAPTCHA_SECRET_KEY') ?: "REPLACE_WITH_RECAPTCHA_SECRET_KEY";

## Require the CAPTCHA on the actions that matter for a moderated public wiki.
$wgCaptchaTriggers['edit']          = false;  # editing is restricted to approved users
$wgCaptchaTriggers['createaccount'] = true;
$wgCaptchaTriggers['badlogin']      = true;

# =============================================================================
# VisualEditor Configuration
# =============================================================================
#
# IMPORTANT (MediaWiki 1.43): Parsoid ships INSIDE MediaWiki core and
# VisualEditor talks to it directly. The old standalone-Parsoid / RESTBase
# setup ($wgVirtualRestConfig['modules']['parsoid'] = [...localhost:8142...])
# is obsolete and MUST NOT be used — it has been removed here on purpose.
# No separate Parsoid container/service is required.

## Enable VisualEditor for all namespaces it is configured for by default.
$wgDefaultUserOptions['visualeditor-enable'] = 1;

## Allow switching to the source (wikitext) editor from VisualEditor.
$wgVisualEditorEnableWikitext = true;

# =============================================================================
# Search Configuration
# =============================================================================

## Use built-in MySQL full-text search by default.
## Consider ElasticSearch (CirrusSearch) for production scale.
$wgDisableInternalSearch = false;

# =============================================================================
# Performance
# =============================================================================

## Compress stored revision text.
$wgCompressRevisions = true;

## NOTE: the former `$wgRevisionStoreType = 'FileStore';` line was removed —
## it is NOT a valid MediaWiki configuration variable and had no effect.

## Enable CDN support (Cloudflare acts as the CDN / reverse cache).
## $wgUseSquid / $wgSquidServers were deprecated (<=1.34); use the modern names.
$wgUseCdn = true;

## MediaWiki runs behind Traefik/Cloudflare, so the client IP arrives via
## X-Forwarded-For. Trust the local reverse proxy; Cloudflare's own ranges are
## handled at the edge. Keep this list tight — only trusted proxies.
$wgCdnServersNoPurge = [
    '127.0.0.1',
    '10.0.0.0/8',
    '172.16.0.0/12',
    '192.168.0.0/16',
];
$wgUsePrivateIPs = false;

# =============================================================================
# Logging
# =============================================================================

## Log errors to file rather than displaying them to users.
$wgShowExceptionDetails = false;  # IMPORTANT: false in production
$wgShowDBErrorBacktrace = false;  # IMPORTANT: false in production

error_reporting( E_ERROR );
ini_set( 'display_errors', '0' );

# =============================================================================
# Job Queue
# =============================================================================
## Do NOT run jobs on web requests in production (keeps page loads fast).
## Run them from cron instead, e.g. every minute on the VPS:
##   * * * * * docker exec wikimedica_app php maintenance/runJobs.php --maxtime=50 >/dev/null 2>&1
## (When the Redis job queue above is enabled, runJobs.php drains that queue.)
$wgJobRunRate = 0;

# =============================================================================
# Additional Notes
# =============================================================================

# For initial installation, run the MediaWiki installer:
#   php /var/www/html/maintenance/install.php \
#     --dbname wikimedica \
#     --dbserver mariadb \
#     --dbuser wikimedica_app \
#     --dbpass "${MEDIAWIKI_DB_PASSWORD}" \
#     --lang de \
#     --pass "${MEDIAWIKI_ADMIN_PASS}" \
#     "Wikimedica" "admin"
#
# After installation, copy this LocalSettings.php into place.
