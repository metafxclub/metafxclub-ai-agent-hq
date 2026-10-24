"""Executable isolated DOM tests. No backend, network, or live writes."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AgentChatFilesFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / 'frontend/src/app/main.js').read_text(encoding='utf-8-sig')
        cls.node = shutil.which('node')
        if not cls.node:
            raise RuntimeError('Node is required for frontend behavior tests')

    def function(self, name):
        match = re.search(r'^(?:async )?function ' + name + r'\(', self.source, re.M)
        self.assertIsNotNone(match, name)
        end = re.search(r'^(?:async )?function ', self.source[match.end():], re.M)
        return self.source[match.start():match.end()+end.start()] if end else self.source[match.start():]

    def probe(self, body):
        names = ['agentAttachmentExtensionsForModel', 'normalizeAgentInputAttachments', 'appendAgentInputAttachments',
                 'appendAgentMessageInline', 'appendAgentMessageMarkdown', 'safeAgentAttachmentName',
                 'getSafeAgentRuntimeArtifactUrl', 'normalizeAgentRuntimeArtifacts', 'agentRuntimeArtifactsFromItem',
                 'normalizeAgentRuntimeMessages', 'safeAgentChatReplyText', 'appendAgentRuntimeArtifactCards',
                 'formatAgentAttachmentBytes', 'agentRuntimeCapabilityTruth', 'normalizeAgentAccessGrant',
                 'normalizeAgentRuntimeStatus', 'explicitAgentRuntimeCapabilityReady', 'normalizeAgentRuntimeThread',
                 'agentAttachmentExtension', 'agentAttachmentMediaType', 'addAgentAttachmentDrafts',
                 'renderAgentAttachmentComposer', 'uploadAgentRuntimeAttachment', 'agentRuntimeAttachmentUploadEndpoint',
                 'agentChatErrorMessage', 'saveAgentRuntimeThreadSettings']
        constants = []
        for name in ['AGENT_RUNTIME_CAPABILITY_MODES', 'AGENT_RUNTIME_BLOCKER_PRESENTATION']:
            constants.append(re.search(r'const '+name+r' = Object.freeze\([\s\S]*?\);',self.source).group())
        script = r'''
const assert=require('node:assert/strict');
const window={location:{href:'http://127.0.0.1:4186/frontend/index.html',origin:'http://127.0.0.1:4186'}};
const AGENT_RUNTIME_ATTACHMENT_HARD_MAX_FILES=8,AGENT_RUNTIME_ATTACHMENT_HARD_MAX_BYTES=20*1024*1024;
const AGENT_RUNTIME_ATTACHMENT_UPLOAD_TEMPLATE='/api/agent-runtime/threads/{threadId}/attachments';
const safeDashboardDisplayText=(value,fallback='',opts={})=>String(value??fallback).slice(0,opts.limit||50000);
const document={createElement:tag=>({tag,dataset:{},attributes:{},children:[],textContent:'',
 append(...children){this.children.push(...children)},appendChild(child){this.children.push(child);return child},
 replaceChildren(...children){this.children=children},setAttribute(key,value){this.attributes[key]=value},addEventListener(){}})};
const textOf=node=>[node.textContent||'',...(node.children||[]).map(textOf)].join(' ');
const find=(node,fn)=>[...(fn(node)?[node]:[]),...(node.children||[]).flatMap(child=>find(child,fn))];
const getSafeExternalHttpUrl=value=>{try{const u=new URL(value);return ['https:','http:'].includes(u.protocol)&&!u.username&&!u.password&&!['localhost','127.0.0.1'].includes(u.hostname)?u.href:''}catch{return ''}};
const state={agentRuntime:{models:[{id:'text-model',inputModalities:['text']}],status:{attachments:{outputReady:true}}},agentChat:{inFlight:false}};
const profiles={};let statusMessage='',posts=0,uploadReply=null;
const getAgentRuntimeProfile=id=>profiles[id]??=( {model:'text-model',attachmentDrafts:[],threads:[]} );
const getSelectedAgentRuntimeThread=profile=>profile.threads[0]||null;
const setAgentChatStatus=(id,message)=>statusMessage=message;
const createAgentChatOpaqueId=prefix=>prefix+'-id';
const els=Object.fromEntries(['modalAgentAttachmentComposer','modalAgentAttachButton','modalAgentAttachmentInput','modalAgentAttachmentPolicy','modalAgentAttachmentDrafts'].map(id=>[id,document.createElement('div')]));
const agentRuntimeThreadEndpoint=(thread,suffix='')=>'/api/agent-runtime/threads/'+thread+suffix;
const readAgentAttachmentBase64=async()=> 'ZmFrZQ==';
const postJson=async()=>{posts++;return uploadReply};
let createdCalls=0,createFails=false;
const createAgentRuntimeThread=async subject=>{createdCalls++;if(createFails)return null;const p=profiles[subject.id],t={id:'new-thread',mode:p.mode,accessGrant:{mode:p.mode,scope:'thread',authorization:'user_selected_mode',grantedAt:'2026-10-23T07:00:00Z'}};p.threads.push(t);return t};
const setAgentRuntimeProfileStatus=(profile,message)=>profile.message=message;
const saveSessionSnapshot=()=>{};
const renderAgentRuntimeConsole=()=>{};
''' + '\n'.join(constants)+'\n'+'\n'.join(self.function(name) for name in names) + '\n(async()=>{\n'+body+'\n})().catch(e=>{process.stderr.write(String(e.stack));process.exitCode=1});'
        result=subprocess.run([self.node,'-'],input=script,capture_output=True,text=True,encoding='utf-8',env={**os.environ,'NODE_OPTIONS':''})
        self.assertEqual(result.returncode,0,result.stderr)

    def test_file_picker_accepts_mq_source_without_image_model_for_multiple_agents(self):
        self.probe(r'''
state.agentRuntime.status.attachments={inputReady:true,fileInputReady:true,imageInputReady:true,acceptedExtensions:['.mq4','.mq5','.mqh','.png'],maxFiles:4,maxBytes:8388608};
for(const id of ['manager','optimization_agent']){
 const subject={id};addAgentAttachmentDrafts(subject,[{name:'strategy.mq4',size:250,type:''},{name:'include.mqh',size:80,type:''}]);
 assert.equal(profiles[id].attachmentDrafts.length,2);assert.equal(profiles[id].attachmentDrafts[0].mediaType,'text/plain');
 assert.equal(els.modalAgentAttachButton.disabled,false);assert.match(els.modalAgentAttachButton.textContent,/Add file/);
 assert.equal(els.modalAgentAttachmentInput.accept,'.mq4,.mq5,.mqh');
 addAgentAttachmentDrafts(subject,[{name:'chart.png',size:250,type:'image/png'}]);assert.equal(profiles[id].attachmentDrafts.length,2);
}
assert.equal(posts,0);
''')

    def test_image_only_and_unconfirmed_file_capability_remain_blocked(self):
        self.probe(r'''
const policy={inputReady:true,fileInputReady:false,imageInputReady:true,acceptedExtensions:['.png','.mq4']};
assert.deepEqual(agentAttachmentExtensionsForModel(policy,false),[]);
assert.deepEqual(agentAttachmentExtensionsForModel(policy,true),['.png']);
assert.deepEqual(agentAttachmentExtensionsForModel({...policy,inputReady:false},true),[]);
assert.deepEqual(agentAttachmentExtensionsForModel({...policy,fileInputReady:true,imageInputReady:false},true),['.mq4']);
''')

    def test_upload_requires_backend_model_or_file_confirmation(self):
        self.probe(r'''
const draft={name:'test.mq4',mediaType:'text/plain',file:{},byteSize:4},policy={uploadTemplate:AGENT_RUNTIME_ATTACHMENT_UPLOAD_TEMPLATE};
uploadReply={ok:true,attachment:{id:'upload_one',fileInputReady:true}};
assert.equal(await uploadAgentRuntimeAttachment('thread-one',draft,policy),'upload_one');
uploadReply={ok:true,attachment:{id:'upload_two',modelInputReady:true}};
assert.equal(await uploadAgentRuntimeAttachment('thread-one',draft,policy),'upload_two');
uploadReply={ok:true,attachment:{id:'upload_three'}};
await assert.rejects(()=>uploadAgentRuntimeAttachment('thread-one',draft,policy),/attachment_upload_not_confirmed/);
''')

    def test_history_preserves_file_chips_and_only_verified_opaque_downloads(self):
        self.probe(r'''
const url='/api/agent-runtime/threads/thread-one/artifacts/file-one';
const [message]=normalizeAgentRuntimeMessages([{role:'user',content:'วิเคราะห์ให้หน่อย',metadata:{attachments:[{fileName:'strategy.mq4',available:true,downloadUrl:url},{fileName:'old.mq5',available:false,downloadUrl:url},{fileName:'fake.txt',available:true,downloadUrl:'file:///C:/secret.txt'}]}}],{name:'Manager'});
assert.equal(message.inputAttachments.length,3);const host=document.createElement('div');appendAgentInputAttachments(host,message.inputAttachments);
assert.equal(find(host,n=>n.tag==='a').length,1);assert.match(textOf(host),/strategy.mq4/);assert.match(textOf(host),/old.mq5/);
''')

    def test_markdown_creates_readable_code_lists_and_source_links(self):
        self.probe(r'''
const host=document.createElement('div');appendAgentMessageMarkdown(host,'## ผลตรวจ\n**Risk** = `1.0`\n- เงื่อนไขแรก\n- อีกเงื่อนไข\n[เอกสาร MQL](https://www.mql5.com/en/docs)\n```mq4\nif (a < b) Print("ok");\n```');
assert.equal(find(host,n=>n.tag==='h4').length,1);assert.equal(find(host,n=>n.tag==='ul').length,1);assert.equal(find(host,n=>n.tag==='li').length,2);
assert.equal(find(host,n=>n.tag==='pre').length,1);assert.equal(find(host,n=>n.tag==='a')[0].href,'https://www.mql5.com/en/docs');
assert.match(textOf(host),/if \(a < b\)/);
''')

    def test_markdown_injection_and_unverified_images_remain_inert(self):
        self.probe(r'''
const host=document.createElement('div');appendAgentMessageMarkdown(host,'<img src=x onerror=alert(1)>\n[bad](javascript:alert(1))\n[local](file:///C:/secret)\n[credential](https://user:password@example.org/)\n![remote](https://example.org/image.png)');
assert.equal(find(host,n=>['img','script','iframe'].includes(n.tag)).length,0);
assert.ok(find(host,n=>n.tag==='a').every(n=>n.href.startsWith('https://example.org/')));
assert.match(textOf(host),/onerror/);assert.doesNotMatch(textOf(host),/ยืนยันแหล่ง/);
''')

    def test_long_code_is_expandable_and_reply_bounded_without_5000_char_cut(self):
        self.probe(r'''
const host=document.createElement('div');appendAgentMessageMarkdown(host,'```mq5\n'+Array.from({length:30},(_,i)=>'line '+i).join('\n')+'\n```');
assert.equal(find(host,n=>n.tag==='details').length,1);assert.match(textOf(host),/30 บรรทัด/);
assert.equal(safeAgentChatReplyText('x'.repeat(6000)).length,6000);assert.equal(safeAgentChatReplyText('x'.repeat(60000)).length,50000);
''')

    def test_images_and_files_have_real_preview_and_download_actions(self):
        self.probe(r'''
const host=document.createElement('div');appendAgentRuntimeArtifactCards(host,[{id:'img-one',available:true,name:'chart.png',mediaType:'image/png',byteSize:900,url:'/api/agent-runtime/threads/t-one/artifacts/img-one'},{id:'file-one',available:true,name:'strategy.mq4',mediaType:'text/plain',byteSize:500,url:'/api/agent-runtime/threads/t-one/artifacts/file-one'}]);
assert.equal(find(host,n=>n.tag==='img').length,1);assert.equal(find(host,n=>n.className==='agent-runtime-artifact-download').length,2);
assert.match(textOf(host),/ดาวน์โหลดรูป/);assert.match(textOf(host),/strategy.mq4/);
const blocked=document.createElement('div');state.agentRuntime.status.attachments.outputReady=false;appendAgentRuntimeArtifactCards(blocked,[{id:'img-one',available:true,url:'/api/agent-runtime/artifacts/img-one'}]);assert.equal(blocked.children.length,0);
''')

    def test_full_permission_does_not_claim_optional_connected_tools(self):
        self.probe(r'''
const runtime={available:true,executionEnabled:true,chatReady:true,toolExecutionEnabled:true,fullAgentReady:true,approvalBrokerReady:true,capabilityModes:[{id:'chat',ready:true},{id:'workspace',ready:true},{id:'full',ready:true}],capabilities:{workspace:{ready:true},computerUse:{ready:false},mcp:{ready:false},plugins:{ready:false}},attachments:{ready:true,fileInputReady:true,imageInputReady:true,acceptedExtensions:['.mq4','.png'],uploadTemplate:AGENT_RUNTIME_ATTACHMENT_UPLOAD_TEMPLATE,maxFiles:4,maxBytes:8388608}};
const status=normalizeAgentRuntimeStatus({ok:true,runtime});assert.equal(agentRuntimeCapabilityTruth(status).fullReady,true);assert.equal(status.capabilities.mcp,false);assert.equal(status.capabilities.computerUse,false);assert.equal(status.attachments.fileInputReady,true);
assert.equal(agentRuntimeCapabilityTruth({...status,fullAgentReady:false}).fullReady,false);assert.equal(agentRuntimeCapabilityTruth({...status,toolExecutionEnabled:false}).fullReady,false);
''')

    def test_grant_must_be_server_record_for_selected_mode(self):
        self.probe(r'''
const grant={mode:'full',scope:'thread',authorization:'user_selected_mode',grantedAt:'2026-10-23T07:00:00Z'};
assert.equal(normalizeAgentAccessGrant(grant,'full').mode,'full');assert.equal(normalizeAgentAccessGrant(grant,'chat'),null);
assert.equal(normalizeAgentAccessGrant({...grant,authorization:'inferred'},'full'),null);assert.equal(normalizeAgentAccessGrant({...grant,grantedAt:''},'full'),null);
assert.equal(normalizeAgentRuntimeThread({id:'thread-one',mode:'full',accessGrant:grant}).accessGrant.mode,'full');
''')

    def test_file_errors_explain_file_limit_instead_of_wrong_busy_message(self):
        self.probe(r'''
assert.match(agentChatErrorMessage({status:409,body:{code:'attachment_requires_workspace'}}),/Workspace/);
assert.equal(agentChatErrorMessage({status:413,body:{kind:'attachment_text_too_large',messageTh:'เลือก Workspace เพื่ออ่านไฟล์เต็ม'}}),'เลือก Workspace เพื่ออ่านไฟล์เต็ม');
assert.equal(agentChatErrorMessage({status:422,body:{error:{code:'invalid_file_content',messageTh:'ไฟล์ไม่ตรงรูปแบบ'}}}),'ไฟล์ไม่ตรงรูปแบบ');
assert.match(agentChatErrorMessage({status:409,body:{kind:'runner_busy'}}),/กำลังตอบ/);
''')

    def test_artifact_gallery_rejects_external_local_and_unavailable_files(self):
        self.probe(r'''
const raw=[{id:'fake-one',available:true,url:'file:///C:/private.txt'},
 {id:'fake-two',available:true,url:'https://example.org/image.png'},
 {id:'fake-three',available:false,url:'/api/agent-runtime/artifacts/a'},
 {id:'fake-four',available:true,url:'/api/agent-runtime/artifacts/a?token=value'},
 {id:'fake-five',available:true,url:'/api/agent-runtime/threads/../a/artifacts/file'}];
assert.deepEqual(normalizeAgentRuntimeArtifacts(raw),[]);
const host=document.createElement('div');appendAgentRuntimeArtifactCards(host,raw);assert.equal(host.children.length,0);
''')

    def test_first_full_access_selection_creates_real_thread_for_ceo_and_agents(self):
        self.probe(r'''
for(const id of ['ceo','manager','optimization_agent']){
 const profile=getAgentRuntimeProfile(id);profile.mode='chat';
 await saveAgentRuntimeThreadSettings({id},'mode','full');
 assert.equal(profile.mode,'full');assert.equal(profile.threads[0].accessGrant.mode,'full');
}
assert.equal(createdCalls,3);assert.equal(posts,0);
''')

    def test_first_permission_selection_rolls_back_when_creation_unconfirmed(self):
        self.probe(r'''
const p=getAgentRuntimeProfile('manager');p.mode='chat';createFails=true;
await saveAgentRuntimeThreadSettings({id:'manager'},'mode','full');
assert.equal(p.mode,'chat');assert.equal(p.threads.length,0);assert.equal(createdCalls,1);
p.actionInFlight=true;await saveAgentRuntimeThreadSettings({id:'manager'},'mode','full');assert.equal(createdCalls,1);
''')


if __name__ == '__main__':
    unittest.main()
