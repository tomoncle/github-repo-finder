#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request
import urllib.error


CONNECT_TIMEOUT = 10  # seconds


def parse_args():
    parser = argparse.ArgumentParser(description='Search recently created GitHub repositories.')
    parser.add_argument('--days', type=int, help='Search repositories created within the last N days UTC.')
    parser.add_argument('--since', help='Search repositories created on or after this UTC date, format YYYY-MM-DD.')
    parser.add_argument('--keywords', nargs='*', default=[], help='Optional keywords to search across name, description, and README.')
    parser.add_argument('--must-have', nargs='*', default=[], help='Required terms that must appear in name, description, or README.')
    parser.add_argument('--exclude', nargs='*', default=[], help='Excluded terms.')
    parser.add_argument('--min-stars', type=int, default=None, help='Minimum GitHub stars.')
    parser.add_argument('--per-page', type=int, default=20, help='Results per page, max 100.')
    parser.add_argument('--max-results', type=int, default=20, help='Maximum results to print.')
    parser.add_argument('--language', default=None, help='Optional language filter.')
    parser.add_argument('--sort', default='created', choices=['created', 'stars', 'updated'], help='GitHub sort field.')
    parser.add_argument('--order', default='desc', choices=['asc', 'desc'], help='Sort order.')
    parser.add_argument('--format', default='table', choices=['table', 'list'], help='Output format.')
    return parser.parse_args()


def utc_today():
    return dt.datetime.now(dt.timezone.utc).date()


def build_created_filter(args):
    if args.since:
        return f'created:>={args.since}'
    if args.days:
        since = utc_today() - dt.timedelta(days=args.days)
        return f'created:>={since.isoformat()}'
    return None


def build_query(args):
    parts = []
    created_filter = build_created_filter(args)
    if created_filter:
        parts.append(created_filter)
    if args.min_stars is not None:
        parts.append(f'stars:>{args.min_stars - 1}')
    if args.language:
        parts.append(f'language:{args.language}')
    for term in args.must_have:
        parts.append(f'"{term}"' if ' ' in term else term)
    for term in args.keywords:
        parts.append(f'"{term}"' if ' ' in term else term)
    for term in args.exclude:
        parts.append(f'-"{term}"' if ' ' in term else f'-{term}')
    q = ' '.join(parts).strip()
    if not q:
        raise SystemExit('Provide --days or --since, and optional keywords.')
    return q


def github_search(query, per_page, sort, order):
    url = 'https://api.github.com/search/repositories?' + urllib.parse.urlencode({
        'q': query,
        'per_page': str(per_page),
        'sort': sort,
        'order': order,
    })
    headers = {
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'codex-github-repo-finder',
    }
    token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
    if token:
        headers['Authorization'] = f'Bearer {token}'

    # Try proxy first (if configured), then fall back to direct connection.
    openers = build_openers()
    last_err = None
    for opener in openers:
        try:
            # Must create a fresh Request for each attempt; a Request object
            # cannot be reused after a failed connection.
            request = urllib.request.Request(url, headers=headers)
            with opener.open(request, timeout=CONNECT_TIMEOUT) as response:
                return json.load(response)
        except (urllib.error.URLError, OSError) as exc:
            last_err = exc
            continue
    raise SystemExit(f'All connection attempts failed. Last error: {last_err}')


def build_openers():
    """Return a list of openers: proxy opener first (if configured), then direct."""
    openers = []
    proxy = os.environ.get('AGENT_HTTP_PROXY')
    if proxy:
        # Ensure the proxy URL has a scheme so urllib can parse it correctly.
        if '://' not in proxy:
            proxy = f'http://{proxy}'
        openers.append(urllib.request.build_opener(urllib.request.ProxyHandler({
            'http': proxy,
            'https': proxy,
        })))
    # Always include a direct (no-proxy) opener as fallback.
    openers.append(urllib.request.build_opener(urllib.request.ProxyHandler({})))
    return openers


def print_table(items):
    rows = []
    for item in items:
        rows.append([
            item['html_url'],
            item['created_at'][:10],
            str(item.get('stargazers_count', 0)),
            item['full_name'],
        ])
    headers = ['项目地址', '创建时间', 'Star数量', '仓库名称']
    widths = [len(header) for header in headers]
    for row in rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))
    print(' | '.join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    print('-+-'.join('-' * width for width in widths))
    for row in rows:
        print(' | '.join(value.ljust(widths[index]) for index, value in enumerate(row)))


def print_list(items):
    for item in items:
        print('\n- full_name:', item['full_name'])
        print('  created_at:', item['created_at'])
        print('  stars:', item.get('stargazers_count', 0))
        print('  description:', item.get('description') or '')
        print('  html_url:', item['html_url'])


def main():
    args = parse_args()
    query = build_query(args)
    data = github_search(query, min(args.per_page, 100), args.sort, args.order)
    items = data.get('items', [])[: args.max_results]
    print(f'Query: {query}')
    print(f'Total matched: {data.get("total_count", 0)}')
    if args.format == 'table':
        print_table(items)
    else:
        print_list(items)


if __name__ == '__main__':
    main()
