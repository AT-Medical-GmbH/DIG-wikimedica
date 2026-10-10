<?php
/**
 * Executes infra/mediawiki/LocalSettings.example.php with minimal MediaWiki
 * stubs and asserts the resulting permission model and key settings.
 * This proves the logic of the config, NOT MediaWiki's behaviour — the latter
 * is verified on staging (docs/editorial/roles-and-permissions.md §5).
 *
 * Usage: php tests/php/localsettings-harness.php infra/mediawiki/LocalSettings.example.php
 */
// Minimal stubs so the example config can be EXECUTED outside MediaWiki.
foreach (['NS_MAIN'=>0,'NS_TEMPLATE'=>10,'NS_CATEGORY'=>14,'NS_HELP'=>12,'NS_PROJECT'=>4,
          'CACHE_ACCEL'=>1,'CACHE_DB'=>2] as $k=>$v) define($k,$v);
function wfLoadSkin($n){ $GLOBALS['loaded'][]="skin:$n"; }
function wfLoadExtension($n){ $GLOBALS['loaded'][]="ext:$n"; }
$loaded=[];
$wgFileExtensions=['png','jpg']; $wgProhibitedFileExtensions=[]; $wgMimeTypeExclusions=[];
$wgGroupPermissions=['*'=>['read'=>true,'edit'=>true,'createaccount'=>true],
  'user'=>['edit'=>true,'upload'=>true,'move'=>true],'autoconfirmed'=>[],
  'sysop'=>['createaccount'=>false],'bureaucrat'=>['userrights'=>true]];
$wgNamespaceProtection=[]; $wgGrantPermissions=[]; $wgGrantPermissionGroups=[]; $wgAvailableRights=[]; $wgAddGroups=[]; $wgRemoveGroups=[];
$wgNamespacesWithSubpages=[]; $wgDefaultUserOptions=[]; $wgCaptchaTriggers=[];
$wgUploadDirectory='/x';
require $argv[1];
$can = fn($g,$r)=> !empty($wgGroupPermissions[$g][$r]);
$checks = [
 'anon cannot edit'              => !$can('*','edit'),
 'anon cannot create account'    => !$can('*','createaccount'),
 'anon can read'                 =>  $can('*','read'),
 'user cannot edit'              => !$can('user','edit'),
 'user cannot upload'            => !$can('user','upload'),
 'autoconfirmed cannot edit'     => !$can('autoconfirmed','edit'),
 'wm-editor can edit (talk)'     =>  $can('wm-editor','edit'),
 'wm-editor lacks content right' => !$can('wm-editor','wm-edit-content'),
 'importbot has content right'   =>  $can('importbot','wm-edit-content') && $can('importbot','bot'),
 'sysop has content right'       =>  $can('sysop','wm-edit-content'),
 'sysop can edit (not inherited)' =>  $can('sysop','edit') && $can('sysop','createpage') && $can('sysop','upload'),
 'bot grant maps content right'  => ($wgGrantPermissions['editpage']['wm-edit-content'] ?? false) === true,
 'main ns protected'             => ($wgNamespaceProtection[0] ?? null) === ['wm-edit-content'],
 'template ns protected'         => ($wgNamespaceProtection[10] ?? null) === ['wm-edit-content'],
 'talk ns NOT protected'         => !isset($wgNamespaceProtection[1]),
 'right registered'              => in_array('wm-edit-content',$wgAvailableRights,true),
 'bureaucrat lost userrights'    => !$can('bureaucrat','userrights'),
 'bureaucrat cannot add sysop'   => !in_array('sysop',$wgAddGroups['bureaucrat'],true),
 'wm-uploader can upload'        =>  $can('wm-uploader','upload'),
 'svg dangerous types blocked'   => in_array('php',$wgProhibitedFileExtensions,true) && in_array('html',$wgProhibitedFileExtensions,true),
 'CDN modern var'                => $wgUseCdn === true,
 'obsolete squid var unset'      => !isset($wgUseSquid),
 'jobs not on web requests'      => $wgJobRunRate === 0,
 'parsoid legacy block absent'   => !isset($wgVirtualRestConfig['modules']['parsoid']),
 'errors hidden'                 => $wgShowExceptionDetails === false,
];
$bad=0; foreach($checks as $n=>$ok){ echo ($ok?'PASS ':'FAIL ').$n."\n"; $bad+=!$ok; }
echo "\n".count($checks)." checks, $bad failed\n";
exit($bad?1:0);
