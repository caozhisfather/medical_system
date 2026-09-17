const { chromium } = require(process.env.PLAYWRIGHT_MODULE_PATH || 'playwright');
const { tmpdir } = require('node:os');
const { join } = require('node:path');
const assert = require('node:assert/strict');

const base = process.env.SKILL_QA_URL || 'http://127.0.0.1:5174';

async function main() {
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.SKILL_QA_BROWSER || undefined,
    args: ['--enable-unsafe-swiftshader'],
  });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const errors = [];
  context.on('page', page => page.on('pageerror', error => errors.push(error.message)));
  const page = await context.newPage();
  const request = context.request;
  const tokens = [];
  let adminHeaders;
  let originals;
  async function json(path, options = {}) {
    const response = await request.fetch(base + path, options);
    assert(response.ok(), `${path}: ${response.status()} ${await response.text()}`);
    return response.json();
  }
  async function login(role) {
    const response = await json('/api/auth/login', { method: 'POST', data: { account: role, password: role + '123', role } });
    tokens.push(response.token);
    return response.token;
  }
  async function installToken(token, role) {
    await page.goto(base + '/login');
    await page.evaluate(({ token, role }) => {
      localStorage.setItem('medical_auth_token', token);
      localStorage.setItem('medical_profile', JSON.stringify({ role, name: 'QA', completed: true }));
    }, { token, role });
  }
  async function screenshot(name) {
    const path = join(tmpdir(), `medical-skills-${name}.png`);
    await page.screenshot({ path, fullPage: true });
    console.log(`screenshot: ${path}`);
  }
  async function canvasPixels() {
    // Read the actual rendered WebGL canvas in the animation frame.
    return page.locator('.anatomy-3d-stage canvas').evaluate(canvas => new Promise(resolve => {
      requestAnimationFrame(() => {
        const output = document.createElement('canvas');
        output.width = canvas.width; output.height = canvas.height;
        const ctx = output.getContext('2d');
        ctx.drawImage(canvas, 0, 0);
        const data = ctx.getImageData(0, 0, output.width, output.height).data;
        const colors = new Set();
        let highlight = 0, hash = 0;
        for (let i = 0; i < data.length; i += 64) {
          const r = data[i], g = data[i + 1], b = data[i + 2];
          colors.add(`${r >> 3},${g >> 3},${b >> 3}`);
          if (r > 140 && g > 95 && g > r * .5 && b < r * .55) highlight++;
          hash = ((hash * 31) + r + g * 3 + b * 7) | 0;
        }
        resolve({ colors: colors.size, highlight, hash, width: output.width, height: output.height });
      });
    }));
  }
  try {
    const adminToken = await login('admin');
    adminHeaders = { Authorization: `Bearer ${adminToken}` };
    originals = await json('/api/admin/skills', { headers: adminHeaders });
    await installToken(adminToken, 'admin');
    await page.goto(base + '/admin/skills');
    await page.getByRole('heading', { name: 'Skill 管理', exact: true }).waitFor();
    await page.keyboard.press('Escape');
    await page.getByRole('button', { name: '测试解剖结构检索', exact: true }).waitFor();
    await screenshot('admin-desktop');
    await page.setViewportSize({ width: 390, height: 844 });
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'mobile page overflow');
    await screenshot('admin-mobile');
    await page.setViewportSize({ width: 1440, height: 1000 });
    for (const skill of originals) {
      await page.getByRole('switch', { name: `${skill.name}启用`, exact: true }).check();
      for (const role of ['学生', '教师', '管理员']) {
        await page.getByRole('checkbox', { name: `${skill.name}允许${role}`, exact: true }).check();
      }
      await page.getByRole('spinbutton', { name: `${skill.name}小时额度`, exact: true }).fill('120');
      const save = page.getByRole('button', { name: `保存${skill.name}`, exact: true });
      if (await save.isEnabled()) {
        await save.click();
        await page.getByRole('status').filter({ hasText: `${skill.name}已保存` }).waitFor();
      }
    }
    await page.reload();
    await page.getByRole('switch', { name: '解剖结构检索启用', exact: true }).waitFor();
    assert(await page.getByRole('switch', { name: '解剖结构检索启用', exact: true }).isChecked(), 'policy not persisted');
    await page.getByRole('button', { name: '测试解剖结构检索', exact: true }).click();
    await page.getByRole('button', { name: '运行测试', exact: true }).click();
    await page.locator('.skill-test-result').filter({ hasText: '成功' }).waitFor();
    await screenshot('admin-test');
    const studentToken = await login('student');
    await installToken(studentToken, 'student');
    await page.goto(base + '/admin/skills');
    await page.waitForURL('**/student/dashboard');
    await page.keyboard.press('Escape');
    await page.goto(base + '/student/anatomy?system=circulatory');
    await page.locator('.body-organ-list').getByRole('button', { name: /心脏/ }).click();
    await page.locator('.organ-structure-list button').first().click();
    await page.locator('.anatomy-3d-stage canvas').waitFor();
    await page.waitForFunction(() => !document.querySelector('.anatomy-3d-overlay'), undefined, { timeout: 60000 });
    await page.waitForTimeout(1500);
    const first = await canvasPixels();
    await page.waitForTimeout(1200);
    const second = await canvasPixels();
    assert(first.colors > 12, `blank model: ${JSON.stringify(first)}`);
    assert(first.hash !== second.hash, 'model not moving');
    assert(first.highlight > 5, `selected structure not highlighted: ${JSON.stringify(first)}`);
    await page.getByRole('button', { name: '空间关系', exact: true }).click();
    await page.locator('.agent-evidence').waitFor({ timeout: 60000 });
    await page.locator('.agent-evidence summary').click();
    assert(await page.locator('.evidence-trace li').count() === 3, 'missing tool trace');
    await screenshot('anatomy-desktop');
    const locate = page.locator('.evidence-actions button').filter({ hasText: '定位' }).first();
    if (await locate.count()) await locate.click();
    await page.getByRole('button', { name: '全屏查看', exact: true }).click();
    await page.waitForFunction(() => !!document.fullscreenElement);
    await page.getByRole('button', { name: '教材详解', exact: true }).first().click();
    await page.locator('.textbook-modal').waitFor();
    assert(await page.locator('.textbook-modal').evaluate(element => document.fullscreenElement.contains(element)), 'textbook outside fullscreen');
    await screenshot('anatomy-fullscreen');
    await page.evaluate(() => document.exitFullscreen());
    await page.getByRole('button', { name: '关闭教材详解', exact: true }).click();
    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForTimeout(1200);
    const mobile = await canvasPixels();
    assert(mobile.colors > 12, 'mobile model blank');
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'anatomy mobile overflow');
    await screenshot('anatomy-mobile');
    await request.put(base + '/api/admin/skills/textbook_search', { headers: adminHeaders, data: { enabled: false, allowed_roles: ['student'], hourly_limit: 120 } });
    const blocked = await json('/api/agent/chat', { method: 'POST', headers: { Authorization: `Bearer ${studentToken}` }, data: { message: '结构：心脏\n讲解组成关系', active_module: 'anatomy_lab', role: 'admin', context: { query: '心脏' } } });
    assert.equal(blocked.skill_results.find(result => result.skill_id === 'textbook_search').status, 'disabled');
    const graph = await json('/api/graph?scope=anatomy');
    assert.equal(graph.nodes.length, 736); assert.equal(graph.edges.length, 1011);
    assert.equal(graph.nodes.filter(node => node.group === 'AnatomyOrgan').length, 48);
    assert.deepEqual(errors, []);
    console.log(JSON.stringify({ result: 'PASS', desktopCanvas: first, movingCanvas: second, mobileCanvas: mobile, errors }));
  } finally {
    const failures = [];
    if (originals) {
      for (const skill of originals) {
        try {
          await json(`/api/admin/skills/${skill.id}`, { method: 'PUT', headers: adminHeaders, data: { enabled: skill.enabled, allowed_roles: skill.allowed_roles, hourly_limit: skill.hourly_limit } });
        } catch (error) { failures.push(error.message); }
      }
    }
    for (const token of tokens) {
      try { await json('/api/auth/logout', { method: 'POST', headers: { Authorization: `Bearer ${token}` } }); }
      catch (error) { failures.push(error.message); }
    }
    await browser.close();
    assert.deepEqual(failures, [], 'QA cleanup failed');
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
