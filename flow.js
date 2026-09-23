// Single-cell / spatial pipeline flow widget.
// Shared by the landing page and the workflows overview page.
// Injects itself into #op-flow. Set window.FLOW_BASE to the site-root-relative
// prefix (e.g. '../') on pages below the site root so the 'all →' links resolve.
(function () {
  // Two kinds of stage:
  //   kind:'choice', pick from alternative components (options + "+N more")
  //   kind:'workflow', one workflow whose steps run in sequence (steps, some
  //                     optional). "optional" is only used here, where a step
  //                     can genuinely be toggled.
  const FLOWS = {
    sc: {
      hint: 'Single-cell multi-omics data.',
      // pills shown next to the toggle — what this flow's data consists of
      modalities: { label: 'Data modalities',
        pills: ['<b>RNA</b>', '<b>Protein</b> (ADT)', '<b>ATAC</b>', '<b>VDJ</b>', '<b>GDO</b>'] },
      stages: [
        { num: 'STEP 01', title: 'Ingestion', kind: 'choice', pick: 'Convert raw data to a standard format',
          options: ['cellranger_multi', 'cellranger_count', 'cellranger_count_atac', 'bd_rhapsody'],
          note: 'Or bring your own count matrix' },
        { num: 'STEP 02', title: 'Process samples', kind: 'workflow', pick: 'Normalize, filter, process',
          steps: [{ name: 'filter cells' }, { name: 'doublet removal', opt: true }, { name: 'normalize + log1p' }, { name: 'highly variable genes' }],
        },
        { num: 'STEP 03', title: 'Integration', kind: 'workflow', pick: 'Remove batch effects',
          href: 'reference/index.html',
          steps: [
            { name: 'integrate', options: ['scVI', 'harmony', 'totalVI'], more: ['scanvi', 'scanorama', 'bbknn'], moreLabel: 'methods' },
            { name: 'find_neighbors' },
            { name: 'leiden' },
            { name: 'umap' },
          ] },
        { num: 'STEP 04', title: 'Downstream', kind: 'choice', pick: 'Perform further analysis',
          options: [
            { name: 'cell-type annotation', options: ['scanvi', 'celltypist', 'singler'], more: ['onclass', 'popv'], moreLabel: 'methods', href: 'guides/index.html' },
            'differential expression', 'rna velocity', 'cell–cell communication',
          ] },
      ],
    },
    sp: {
      hint: 'Spatial transcriptomics data.',
      // pills shown next to the toggle — spatial has one data type (transcriptomics)
      // across several instrument platforms, so these tag platforms, not modalities
      modalities: { label: 'Technology platforms',
        pills: ['<b>Visium</b>', '<b>Visium HD</b>', '<b>Xenium</b>', '<b>CosMx</b>', '<b>AVITI</b>'] },
      stages: [
        { num: 'STEP 01', title: 'Ingestion', kind: 'choice', pick: 'Convert raw data to a standard format',
          options: ['visium · spaceranger', 'visium HD · spaceranger', 'xenium', 'cosmx', 'aviti'],
          note: 'Or bring your own count matrix' },
        { num: 'STEP 02', title: 'Process samples', kind: 'workflow', pick: 'Normalize, filter, process',
          steps: [{ name: 'filter cells' }, { name: 'normalize + log1p' }, { name: 'highly variable genes' }],
        },
        { num: 'STEP 03', title: 'Integration', kind: 'workflow', pick: 'Remove batch effects',
          href: 'reference/index.html',
          steps: [
            { name: 'integrate', options: ['scVI', 'harmony', 'totalVI'], more: ['scanvi', 'scanorama', 'bbknn'], moreLabel: 'methods' },
            { name: 'find_neighbors' },
            { name: 'leiden' },
            { name: 'umap' },
          ] },
        { num: 'STEP 04', title: 'Downstream', kind: 'choice', pick: 'Perform further analysis',
          options: [
            { name: 'cell-type annotation', options: ['scanvi', 'celltypist', 'singler'], more: ['onclass', 'popv'], moreLabel: 'methods', href: 'guides/index.html' },
            'differential expression', 'cell–cell communication', 'spatial domains', 'niche domains',
          ] },
      ],
    },
  };
  // Render the widget shell into its mount point (both host pages carry only
  // <div id="op-flow"></div>), unless the page already ships the markup itself.
  // Mount opt-ins: data-layout="vertical" stacks the stages top-to-bottom;
  // data-detailed="true" adds the optional stages the landing overview omits.
  var mount = document.getElementById('op-flow');
  var vertical = !!(mount && mount.dataset.layout === 'vertical');
  var detailed = !!(mount && mount.dataset.detailed === 'true');
  var showModalities = !!(mount && mount.dataset.modalities === 'true');
  if (mount && !document.getElementById('flow')) {
    mount.innerHTML =
      '<div class="flow-card">' +
      '<div class="seg-row">' +
      '<div class="seg" id="flow-seg">' +
      '<button class="on" data-flow="sc">Single-cell</button>' +
      '<button data-flow="sp">Spatial</button>' +
      '</div>' +
      (showModalities ? '<div class="modalities" id="flow-modalities"></div>' : '') +
      '</div>' +
      '<div class="flow-hint" id="flow-hint"></div>' +
      '<div class="flow-scroll"><div class="flow' + (vertical ? ' vertical' : '') + '" id="flow"></div></div>' +
      '</div>';
  }

  // Detailed variant (workflows page): surface the two optional stages that
  // the landing overview intentionally leaves out.
  if (detailed) {
    var demux = {
      title: 'Demultiplexing', kind: 'choice', pick: 'Split multiplexed samples', opt: true,
      options: ['bcl2fastq', 'bcl-convert', 'cellranger mkfastq'],
    };
    var qcReport = {
      title: 'QC report', kind: 'choice', pick: 'Inspect data quality', opt: true,
      options: ['generate_qc_report'],
      note: 'Select filtering thresholds'
    };
    // single-cell: demux before ingestion, QC report between ingestion and processing
    FLOWS.sc.stages = [demux, FLOWS.sc.stages[0], qcReport].concat(FLOWS.sc.stages.slice(1));
    // spatial: QC report after ingestion (imaging-based platforms have no demux step)
    FLOWS.sp.stages = [FLOWS.sp.stages[0], qcReport].concat(FLOWS.sp.stages.slice(1));
  }

  const flowEl = document.getElementById('flow');
  const flowHint = document.getElementById('flow-hint');
  if (!flowEl) return;

  function chip(t) {
    var cls = 'chip' + (t.alt ? ' alt' : '') + (t.opt ? ' opt' : '');
    return '<span class="' + cls + '">' + t.name +
      (t.opt ? ' <em>optional</em>' : '') + '</span>';
  }
  // "+N more" chip that expands its hidden alternatives in place
  function moreCluster(items, href, label) {
    var hidden = items.map(function (n) { return chip({ name: n, alt: true }); }).join('');
    var link = href ? '<a class="chip link" href="' + (window.FLOW_BASE || '') + href + '">all →</a>' : '';
    var lbl = label || 'more';
    return '<span class="chip more" data-count="' + items.length + '" data-label="' + lbl + '">+' + items.length + ' ' + lbl + '</span>' +
      '<span class="more-wrap" hidden>' + hidden + link + '</span>';
  }
  // a labeled, bordered group of alternatives (e.g. "integrate" ->
  // scVI/harmony/totalVI, or "cell-type annotation" -> its methods) —
  // shared by workflow steps and choice options so both read the same way.
  function renderSubstep(label, options, more, href, moreLabel) {
    var optChips = options.map(function (n) { return chip({ name: n, alt: true }); }).join('');
    var m = (more && more.length) ? moreCluster(more, href, moreLabel) : '';
    return '<span class="substep"><span class="substep-label">' + label + '</span>' +
      '<span class="chips">' + optChips + m + '</span></span>';
  }
  function renderStage(s) {
    var num = s.opt ? '<div class="num opt">optional</div>' : '<div class="num">' + s.num + '</div>';
    var head = '<span class="station"></span>' +
      num + '<h4>' + s.title + '</h4>' +
      '<div class="pick">' + s.pick + '</div>';
    var stageCls = 'stage' + (s.opt ? ' optional' : '');
    if (s.kind === 'workflow') {
      var parts = [];
      s.steps.forEach(function (st, i) {
        if (i) parts.push('<span class="seq-arrow">→</span>');
        if (st.options) {
          // a choice step within the sequence (e.g. "integrate")
          parts.push(renderSubstep(st.name, st.options, st.more, s.href, st.moreLabel));
        } else {
          parts.push(chip(st));
        }
      });
      var wfNote = s.note ? '<div class="stage-note">' + s.note + '</div>' : '';
      return '<div class="' + stageCls + '">' + head + '<div class="seq">' + parts.join('') + '</div>' + wfNote + '</div>';
    }
    var opts = s.options.map(function (o) {
      if (typeof o === 'string') return chip({ name: o, alt: true });
      return renderSubstep(o.name, o.options, o.more, o.href, o.moreLabel);
    }).join('');
    var more = (s.more && s.more.length) ? moreCluster(s.more, s.href, s.moreLabel) : '';
    var note = s.note ? '<div class="stage-note">' + s.note + '</div>' : '';
    return '<div class="' + stageCls + '">' + head + '<div class="chips">' + opts + more + '</div>' + note + '</div>';
  }
  const flowModalities = document.getElementById('flow-modalities');
  function renderFlow(which) {
    const f = FLOWS[which];
    flowHint.textContent = f.hint;
    flowEl.style.setProperty('--path', which === 'sp' ? 'var(--spatial)' : 'var(--accent-ink)');
    flowEl.innerHTML = f.stages.map(renderStage).join('');
    if (flowModalities && f.modalities) {
      flowModalities.innerHTML = '<span class="modalities-label">' + f.modalities.label + '</span>' +
        f.modalities.pills.map(function (p) { return '<span class="m">' + p + '</span>'; }).join('');
    }
    flowEl.querySelectorAll('.chip.more').forEach(function (m) {
      m.onclick = function () {
        var wrap = m.nextElementSibling;
        var open = !wrap.hidden;
        wrap.hidden = open;
        m.textContent = open ? ('+' + m.dataset.count + ' ' + m.dataset.label) : 'show less';
      };
    });
  }
  document.querySelectorAll('#flow-seg button').forEach(function (b) {
    b.onclick = function () {
      document.querySelectorAll('#flow-seg button').forEach(function (x) {
        x.classList.toggle('on', x === b);
      });
      renderFlow(b.dataset.flow);
    };
  });
  renderFlow('sc');
})();
